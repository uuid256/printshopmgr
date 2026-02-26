"""Customer CRUD views with HTMX search support."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.mixins import role_required
from accounts.models import Role

from .models import Customer, CustomerType


@login_required
def customer_list(request):
    customers = Customer.objects.filter(is_active=True).select_related("customer_type")
    q = request.GET.get("q", "").strip()
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    return render(request, "customers/list.html", {"customers": customers, "q": q})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, "customers/detail.html", {"customer": customer})


@role_required(Role.COUNTER, Role.OWNER)
def customer_create(request):
    from .forms import CustomerForm

    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            return redirect("customers:detail", pk=customer.pk)
    else:
        form = CustomerForm()
    return render(request, "customers/form.html", {"form": form, "action": "สร้างลูกค้าใหม่"})


@role_required(Role.COUNTER, Role.OWNER)
def customer_edit(request, pk):
    from .forms import CustomerForm

    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect("customers:detail", pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, "customers/form.html", {"form": form, "action": "แก้ไขข้อมูลลูกค้า"})


@login_required
def customer_autocomplete(request):
    """JSON endpoint for the customer select-autocomplete widget."""
    q = request.GET.get("q", "").strip()
    if len(q) < 1:
        return JsonResponse([], safe=False)
    customers = (
        Customer.objects.filter(
            Q(name__icontains=q) | Q(phone__icontains=q),
            is_active=True,
        )
        .values("id", "name", "phone")[:12]
    )
    return JsonResponse(list(customers), safe=False)


@login_required
def customer_search(request):
    """HTMX endpoint: returns a partial list of matching customers."""
    q = request.GET.get("q", "").strip()
    customers = []
    if len(q) >= 2:
        customers = Customer.objects.filter(
            Q(name__icontains=q) | Q(phone__icontains=q),
            is_active=True,
        )[:10]
    return render(request, "customers/partials/search_results.html", {"customers": customers, "q": q})
