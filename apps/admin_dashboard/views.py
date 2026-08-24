from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.branches.models import Branch
from apps.offers.models import Offer


STATUS_ORDER = ['Active', 'Scheduled', 'Inactive', 'Expired']
STATUS_COLORS = {
    'Active': '#477cff',
    'Scheduled': '#9257ec',
    'Inactive': '#ff9c20',
    'Expired': '#ff655d',
}


def _start_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _auto_update_statuses(self):
        now = timezone.now()
        Offer.objects.filter(is_active=False, start_date__lte=now, end_date__gte=now).update(is_active=True)
        Offer.objects.filter(is_active=True, end_date__lt=now).update(is_active=False)

    def _scoped_offers(self):
        user = self.request.user
        qs = Offer.objects.all().prefetch_related('offerbranch_set__branch')
        if user.role == 'BRANCH_MGR' and user.managed_branch:
            qs = qs.filter(branches=user.managed_branch)
        return qs

    def _scoped_branches(self):
        user = self.request.user
        qs = Branch.objects.all()
        if user.role == 'BRANCH_MGR' and user.managed_branch:
            qs = qs.filter(id=user.managed_branch.id)
        return qs

    def _get_status(self, offer, now):
        if now > offer.end_date:
            return 'Expired'
        if now < offer.start_date:
            return 'Scheduled'
        return 'Active' if offer.is_active else 'Inactive'

    def _relative_time(self, dt, now):
        diff = now - dt
        minutes = int(diff.total_seconds() // 60)
        if minutes < 1:
            return 'Just now'
        if minutes < 60:
            return f'{minutes}m ago'
        hours = minutes // 60
        if hours < 24:
            return f'{hours}h ago'
        days = hours // 24
        if days < 7:
            return f'{days}d ago'
        return dt.strftime('%d %b %Y')

    def get(self, request):
        self._auto_update_statuses()
        now = timezone.now()
        offers = list(self._scoped_offers())
        branches = list(self._scoped_branches())

        weekday = now.weekday()
        week_start = _start_of_day(now) - timedelta(days=weekday)
        week_end = week_start + timedelta(days=7)
        prev_start = week_start - timedelta(days=7)
        prev_end = week_start

        def in_range(dt, start, end):
            return start <= dt < end

        # ---- status distribution
        status_counts = {key: 0 for key in STATUS_ORDER}
        for offer in offers:
            status_counts[self._get_status(offer, now)] += 1

        total = len(offers)
        status_distribution = [
            {
                'label': key,
                'value': status_counts[key],
                'pct': round((status_counts[key] / total) * 100, 1) if total else 0,
                'color': STATUS_COLORS[key],
            }
            for key in STATUS_ORDER
        ]

        # ---- metrics
        total_views = sum(offer.view_count for offer in offers)

        offers_this_week = [o for o in offers if in_range(o.created_at, week_start, week_end)]
        offers_last_week = [o for o in offers if in_range(o.created_at, prev_start, prev_end)]
        branches_this_week = [b for b in branches if in_range(b.created_at, week_start, week_end)]
        branches_last_week = [b for b in branches if in_range(b.created_at, prev_start, prev_end)]
        active_created_this_week = [o for o in offers_this_week if self._get_status(o, now) == 'Active']
        active_created_last_week = [o for o in offers_last_week if self._get_status(o, now) == 'Active']

        def pct_delta(cur, prev):
            if prev == 0:
                return 0 if cur == 0 else 100
            return round(((cur - prev) / prev) * 100, 1)

        metrics = [
            {
                'key': 'total_branches',
                'label': 'Total Branches',
                'value': len(branches),
                'delta': f'+{len(branches_this_week)} this week',
                'tone': 'violet',
            },
            {
                'key': 'active_offers',
                'label': 'Active Offers',
                'value': status_counts['Active'],
                'delta': f'+{len(active_created_this_week)} this week',
                'tone': 'orange',
            },
            {
                'key': 'offer_posts',
                'label': 'Offer Posts',
                'value': len(offers),
                'delta': f'+{len(offers_this_week)} this week',
                'tone': 'purple',
            },
            {
                'key': 'total_views',
                'label': 'Total Views',
                'value': total_views,
                'delta': f'+{pct_delta(len(offers_this_week), len(offers_last_week))}% this week',
                'tone': 'red',
            },
        ]

        # ---- 7-day overview
        labels, active_series, posts_series = [], [], []
        for i in range(7):
            day_start = week_start + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            labels.append(day_start.strftime('%b %d'))
            active_series.append(
                sum(1 for o in offers if o.start_date <= day_end and o.end_date >= day_start)
            )
            posts_series.append(
                sum(1 for o in offers if in_range(o.created_at, day_start, day_end))
            )

        overview = {'labels': labels, 'active': active_series, 'posts': posts_series}

        # ---- top performing branches (via prefetched offer branches)
        branch_offers = defaultdict(list)
        for offer in offers:
            seen = set()
            for ob in offer.offerbranch_set.all():
                if ob.branch_id in seen:
                    continue
                seen.add(ob.branch_id)
                branch_offers[ob.branch_id].append(offer)

        top_branches = []
        for branch in branches:
            branch_list = branch_offers.get(branch.id, [])
            active_list = [o for o in branch_list if self._get_status(o, now) == 'Active']
            cur_count = sum(1 for o in branch_list if in_range(o.created_at, week_start, week_end))
            prev_count = sum(1 for o in branch_list if in_range(o.created_at, prev_start, prev_end))
            growth = round(((cur_count - prev_count) / prev_count) * 100, 1) if prev_count else (100.0 if cur_count else 0.0)
            top_branches.append({
                'name': branch.name,
                'address': branch.address,
                'initials': ''.join(word[0] for word in branch.name.split()[:2]).upper() or branch.name[:2].upper(),
                'offer_count': len(active_list),
                'views': sum(o.view_count for o in active_list),
                'growth': growth,
            })

        top_branches.sort(key=lambda b: (b['offer_count'], b['views']), reverse=True)
        top_branches = top_branches[:5]

        # ---- recent offer posts
        recent = sorted(offers, key=lambda o: o.created_at, reverse=True)[:4]
        recent_posts = [
            {
                'title': o.title,
                'place': o.offerbranch_set.first().branch.name if o.offerbranch_set.first() else '—',
                'status': self._get_status(o, now),
                'time_label': self._relative_time(o.created_at, now),
                'image': o.image.url if o.image else '',
            }
            for o in recent
        ]

        return Response({
            'metrics': metrics,
            'overview': overview,
            'top_branches': top_branches,
            'recent_posts': recent_posts,
            'status_distribution': status_distribution,
        })
