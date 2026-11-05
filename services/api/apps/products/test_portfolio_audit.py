from django.test import TestCase
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from unittest.mock import patch

from apps.identity.models import NexoraUser
from .models import PortfolioAuditEvent, ProductPortfolioEntry
from .portfolio_audit import save_portfolio_entry


class PortfolioAuditServiceTests(TestCase):
    def setUp(self):
        self.actor = NexoraUser.objects.create_user()
        self.entry = ProductPortfolioEntry(
            key="audit-test-app",
            name="Audit Test App",
            entry_type=ProductPortfolioEntry.EntryType.APPLICATION,
            category="Test",
            lifecycle_status=ProductPortfolioEntry.LifecycleStatus.PLANNED,
            decision_status=ProductPortfolioEntry.DecisionStatus.CONFIRMED,
            priority=ProductPortfolioEntry.Priority.CORE,
            delivery_model=ProductPortfolioEntry.DeliveryModel.STANDALONE,
        )

    def test_create_and_update_are_audited_with_actor_and_field_diff(self):
        entry, created = save_portfolio_entry(
            entry=self.entry,
            source=PortfolioAuditEvent.Source.ADMIN,
            actor=self.actor,
        )
        self.assertTrue(created)
        first = PortfolioAuditEvent.objects.get(entry=entry)
        self.assertEqual(first.action, PortfolioAuditEvent.Action.CREATED)
        self.assertEqual(first.actor_id, self.actor.pk)
        self.assertIn("name", first.changes)

        entry.name = "Renamed Audit Test App"
        entry.description = "Updated description"
        entry, changed = save_portfolio_entry(
            entry=entry,
            source=PortfolioAuditEvent.Source.ADMIN,
            actor=self.actor,
        )
        self.assertTrue(changed)
        latest = PortfolioAuditEvent.objects.latest("occurred_at")
        self.assertEqual(latest.action, PortfolioAuditEvent.Action.UPDATED)
        self.assertEqual(set(latest.changes), {"name", "description"})
        self.assertEqual(latest.changes["name"]["before"], "Audit Test App")
        self.assertEqual(latest.changes["name"]["after"], "Renamed Audit Test App")

    def test_portfolio_key_rename_is_audited_and_updates_event_snapshot(self):
        entry, _ = save_portfolio_entry(
            entry=self.entry,
            source=PortfolioAuditEvent.Source.ADMIN,
            actor=self.actor,
        )
        entry.key = "renamed-audit-test-app"
        entry, changed = save_portfolio_entry(
            entry=entry,
            source=PortfolioAuditEvent.Source.ADMIN,
            actor=self.actor,
        )

        self.assertTrue(changed)
        self.assertEqual(entry.key, "renamed-audit-test-app")
        event = PortfolioAuditEvent.objects.latest("occurred_at")
        self.assertEqual(event.entry_key, "renamed-audit-test-app")
        self.assertEqual(
            event.changes["key"],
            {"before": "audit-test-app", "after": "renamed-audit-test-app"},
        )

    def test_noop_save_does_not_create_noise(self):
        entry, _ = save_portfolio_entry(
            entry=self.entry,
            source=PortfolioAuditEvent.Source.MANIFEST,
        )
        count = PortfolioAuditEvent.objects.count()
        _, changed = save_portfolio_entry(
            entry=entry,
            source=PortfolioAuditEvent.Source.MANIFEST,
        )
        self.assertFalse(changed)
        self.assertEqual(PortfolioAuditEvent.objects.count(), count)

    def test_audit_event_rejects_application_level_mutation_and_delete(self):
        entry, _ = save_portfolio_entry(
            entry=self.entry,
            source=PortfolioAuditEvent.Source.MANIFEST,
        )
        event = PortfolioAuditEvent.objects.get(entry=entry)
        event.actor_label = "tampered"
        with self.assertRaises(ValueError):
            event.save()
        with self.assertRaises(ValueError):
            event.delete()


class OfficePortfolioAuditApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = NexoraUser.objects.create_user()
        self.staff.is_staff = True
        self.staff.save(update_fields=("is_staff",))
        self.staff.groups.add(Group.objects.create(name="Office Auditor"))
        self.regular = NexoraUser.objects.create_user()
        self.entry = ProductPortfolioEntry(
            key="audit-api-app",
            name="Audit API App",
            entry_type=ProductPortfolioEntry.EntryType.APPLICATION,
            category="Test",
            lifecycle_status=ProductPortfolioEntry.LifecycleStatus.PLANNED,
            decision_status=ProductPortfolioEntry.DecisionStatus.CONFIRMED,
            priority=ProductPortfolioEntry.Priority.CORE,
            delivery_model=ProductPortfolioEntry.DeliveryModel.STANDALONE,
        )
        save_portfolio_entry(
            entry=self.entry,
            source=PortfolioAuditEvent.Source.MANIFEST,
        )

    def test_audit_api_requires_staff_and_verified_email(self):
        anonymous = self.client.get("/api/v1/office/audit/")
        self.assertEqual(anonymous.status_code, 401)

        self.client.force_authenticate(user=self.regular)
        with patch("apps.identity.office_access.OfficeAccessPermission.has_permission", return_value=True):
            denied = self.client.get("/api/v1/office/audit/")
        self.assertEqual(denied.status_code, 403)

        self.client.force_authenticate(user=self.staff)
        with patch("apps.identity.office_access.OfficeAccessPermission.has_permission", return_value=True):
            allowed = self.client.get("/api/v1/office/audit/")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.data["count"], 1)
        self.assertEqual(allowed.data["results"][0]["entry_key"], "audit-api-app")

    def test_audit_api_rejects_invalid_filters_and_bounds_page_size(self):
        self.client.force_authenticate(user=self.staff)
        with patch("apps.identity.office_access.OfficeAccessPermission.has_permission", return_value=True):
            invalid = self.client.get("/api/v1/office/audit/?action=deleted")
            bounded = self.client.get("/api/v1/office/audit/?limit=1000")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(bounded.status_code, 200)
        self.assertEqual(bounded.data["limit"], 100)
