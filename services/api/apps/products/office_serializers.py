from rest_framework import serializers

from .models import ProductPortfolioEntry


class PortfolioParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPortfolioEntry
        fields = ("key", "name", "entry_type")


class PortfolioChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPortfolioEntry
        fields = (
            "key", "name", "category", "lifecycle_status",
            "decision_status", "priority", "delivery_model",
        )


class PortfolioEntrySerializer(serializers.ModelSerializer):
    parent = PortfolioParentSerializer(read_only=True)
    activation_product_key = serializers.CharField(
        source="activation_product.key", read_only=True, default=None
    )
    module_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductPortfolioEntry
        fields = (
            "id", "key", "name", "entry_type", "category", "description",
            "parent", "lifecycle_status", "decision_status", "priority",
            "delivery_model", "activation_product_key", "module_count",
            "sort_order", "created_at", "updated_at",
        )


class PortfolioEntryDetailSerializer(PortfolioEntrySerializer):
    modules = PortfolioChildSerializer(many=True, read_only=True)

    class Meta(PortfolioEntrySerializer.Meta):
        fields = PortfolioEntrySerializer.Meta.fields + ("modules",)


from .models import PortfolioAuditEvent


class OfficePortfolioAuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioAuditEvent
        fields = (
            "id", "entry_key", "entry_name", "action", "source",
            "actor_label", "changes", "occurred_at",
        )
        read_only_fields = fields
