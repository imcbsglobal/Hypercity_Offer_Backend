from datetime import timedelta
import json

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from .models import CustomForm, CustomFormField, CustomFormResponse


class CustomFormsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            phone='9000001000', name='Form Staff', password='password', is_staff=True, role='MARKETING'
        )
        self.customer = User.objects.create_user(phone='9000001001', name='Customer', password='password')
        self.client.force_authenticate(self.staff)
        self.fields = [
            {'position': 0, 'field_type': 'SHORT_TEXT', 'label': 'Name', 'required': True},
            {'position': 1, 'field_type': 'EMAIL', 'label': 'Email', 'required': True},
            {'position': 2, 'field_type': 'PHONE', 'label': 'Phone'},
            {'position': 3, 'field_type': 'NUMBER', 'label': 'Age', 'validation': {'min': 18, 'max': 100}},
            {'position': 4, 'field_type': 'DATE', 'label': 'Date'},
            {'position': 5, 'field_type': 'SINGLE_CHOICE', 'label': 'Plan', 'choices': ['Basic', 'Premium']},
            {'position': 6, 'field_type': 'MULTIPLE_CHOICE', 'label': 'Topics', 'choices': ['News', 'Offers']},
            {'position': 7, 'field_type': 'DROPDOWN', 'label': 'City', 'choices': ['Kochi', 'Kozhikode']},
            {'position': 8, 'field_type': 'RATING', 'label': 'Rating', 'validation': {'min': 1, 'max': 5}},
            {'position': 9, 'field_type': 'LONG_TEXT', 'label': 'Feedback'},
        ]

    def create_form(self):
        response = self.client.post('/api/custom-forms/', {
            'title': 'Customer Survey',
            'description': 'Tell us what you think.',
            'fields': self.fields,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_staff_can_create_publish_and_public_can_submit_all_field_types(self):
        form_data = self.create_form()
        form_id = form_data['id']
        publish = self.client.post(f'/api/custom-forms/{form_id}/publish/')
        self.assertEqual(publish.status_code, 200, publish.data)
        self.assertEqual(publish.data['status'], 'PUBLISHED')

        self.client.force_authenticate(user=None)
        public = self.client.get(f"/api/public/forms/{form_data['public_id']}/")
        self.assertEqual(public.status_code, 200)
        keys = {field['field_type']: field['field_key'] for field in public.data['fields']}
        answers = {
            keys['SHORT_TEXT']: 'Asha',
            keys['EMAIL']: 'asha@example.com',
            keys['PHONE']: '+91 9876543210',
            keys['NUMBER']: 30,
            keys['DATE']: '2026-10-01',
            keys['SINGLE_CHOICE']: 'Premium',
            keys['MULTIPLE_CHOICE']: ['News', 'Offers'],
            keys['DROPDOWN']: 'Kochi',
            keys['RATING']: 5,
            keys['LONG_TEXT']: 'Great service',
        }
        submitted = self.client.post(f"/api/public/forms/{form_data['public_id']}/responses/", {'answers': answers}, format='json')
        self.assertEqual(submitted.status_code, 201, submitted.data)
        self.assertEqual(CustomFormResponse.objects.count(), 1)
        self.assertEqual(len(CustomFormResponse.objects.first().schema_snapshot), 10)

    def test_draft_is_private_and_published_form_is_locked(self):
        form_data = self.create_form()
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f"/api/public/forms/{form_data['public_id']}/").status_code, 404)

        self.client.force_authenticate(self.staff)
        self.client.post(f"/api/custom-forms/{form_data['id']}/publish/")
        update = self.client.patch(f"/api/custom-forms/{form_data['id']}/", {'title': 'Changed'}, format='json')
        self.assertEqual(update.status_code, 400)

    def test_validation_and_closed_forms_reject_public_responses(self):
        form_data = self.create_form()
        self.client.post(f"/api/custom-forms/{form_data['id']}/publish/")
        self.client.force_authenticate(user=None)
        public = self.client.get(f"/api/public/forms/{form_data['public_id']}/").data
        email_key = next(field['field_key'] for field in public['fields'] if field['field_type'] == 'EMAIL')
        invalid = self.client.post(f"/api/public/forms/{form_data['public_id']}/responses/", {'answers': {email_key: 'not-an-email'}}, format='json')
        self.assertEqual(invalid.status_code, 400)

        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post(f"/api/custom-forms/{form_data['id']}/close/").status_code, 200)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f"/api/public/forms/{form_data['public_id']}/").status_code, 404)

    def test_non_staff_cannot_manage_forms_and_staff_can_export_responses(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get('/api/custom-forms/').status_code, 403)

        self.client.force_authenticate(self.staff)
        form_data = self.create_form()
        form = CustomForm.objects.get(id=form_data['id'])
        field = form.fields.first()
        CustomFormResponse.objects.create(form=form, answers={str(field.field_key): 'Value'}, schema_snapshot=[])
        export = self.client.get(f'/api/custom-forms/{form.id}/export/')
        self.assertEqual(export.status_code, 200)
        self.assertEqual(export['Content-Type'], 'text/csv')

    def test_staff_can_delete_a_published_form_and_its_responses(self):
        form_data = self.create_form()
        self.client.post(f"/api/custom-forms/{form_data['id']}/publish/")
        form = CustomForm.objects.get(id=form_data['id'])
        CustomFormResponse.objects.create(form=form, answers={}, schema_snapshot=[])

        deleted = self.client.delete(f"/api/custom-forms/{form.id}/")

        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(CustomForm.objects.filter(id=form.id).exists())
        self.assertEqual(CustomFormResponse.objects.count(), 0)

    def test_multipart_draft_save_preserves_json_fields(self):
        response = self.client.post('/api/custom-forms/', {
            'title': 'Multipart form',
            'description': 'Has a logo upload path.',
            'accent_color': '#1A7A48',
            'confirmation_message': 'Thanks!',
            'fields': json.dumps(self.fields),
        }, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data['fields']), len(self.fields))
