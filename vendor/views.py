from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status, viewsets
from .serializers import *
from .models import *


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "per_page"
    max_page_size = 100


class VendorProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(
                {
                    "results": serializer.data,
                    "count": self.paginator.page.paginator.count,
                }
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data, "count": len(serializer.data)})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(
            {"message": "Product created successfully", "product": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(
            {"message": "Product updated successfully", "product": serializer.data}
        )

    @action(detail=False, methods=["post"], url_path="upload/(?P<vendor_id>[^/.]+)")
    def upload_products(self, request, vendor_id=None):
        if "file" not in request.FILES:
            return Response(
                {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]
        serializer = ProductUploadSerializer(data={"file": file})

        if serializer.is_valid():
            serializer.save(vendor_id=vendor_id)
            return Response(
                {
                    "message": "Products uploaded successfully",
                    "count": (
                        serializer.instance.count()
                        if hasattr(serializer, "instance")
                        else 0
                    ),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": "Upload failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AdminProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        vendor_id = self.request.query_params.get("vendor_id")
        if vendor_id:
            queryset = queryset.filter(vendor__id=vendor_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(
                {
                    "results": serializer.data,
                    "count": self.paginator.page.paginator.count,
                }
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data, "count": len(serializer.data)})

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        vendor_id = data.get("vendor")

        try:
            vendor = (
                Vendor.objects.get(id=vendor_id)
                if vendor_id
                else request.user.vendor_profile
            )
            data["vendor"] = vendor.id
        except (Vendor.DoesNotExist, AttributeError):
            return Response(
                {"error": "Vendor not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(
            {"message": "Product created successfully", "product": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        vendor_id = data.get("vendor")

        if vendor_id:
            try:
                vendor = Vendor.objects.get(id=vendor_id)
                data["vendor"] = vendor.id
            except Vendor.DoesNotExist:
                return Response(
                    {"error": "Vendor not found"}, status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(
            {"message": "Product updated successfully", "product": serializer.data}
        )

    @action(detail=False, methods=["post"], url_path="upload/(?P<vendor_id>[^/.]+)")
    def upload_products(self, request, vendor_id=None):
        if "file" not in request.FILES:
            return Response(
                {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response(
                {"error": "Vendor not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]
        serializer = ProductUploadSerializer(data={"file": file})

        if serializer.is_valid():
            serializer.save(vendor_id=vendor.id)
            return Response(
                {
                    "message": "Products uploaded successfully",
                    "count": (
                        serializer.instance.count()
                        if hasattr(serializer, "instance")
                        else 0
                    ),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": "Upload failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
