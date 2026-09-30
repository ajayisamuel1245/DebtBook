from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from .forms import SignupForm, LoginForm, CustomerForm,LedgerEntryForm
from .models import Customer, LedgerEntry
from urllib.parse import quote
from django.urls import reverse
from django.db.models.functions import TruncMonth
from django.contrib.auth import logout

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            trader_profile = form.save()
            login(request, trader_profile.user)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'ledger/signup.html', {'form': form})


def login_view(request):
    error = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            error = "Incorrect email or password."
    else:
        form = LoginForm()
    return render(request, 'ledger/login.html', {'form': form, 'error': error})


from django.db.models import Sum
from django.utils import timezone


@login_required
def dashboard_view(request):
    trader = request.user.traderprofile
    customers = Customer.objects.filter(trader=trader)

    # Total owed + customers owing — computed per customer since balance() isn't a DB field
    total_owed = 0
    customers_owing_count = 0
    debtor_balances = []
    for c in customers:
        bal = c.balance()
        if bal > 0:
            total_owed += bal
            customers_owing_count += 1
            debtor_balances.append((c, bal))

    biggest_debtors = sorted(debtor_balances, key=lambda x: x[1], reverse=True)[:5]

    now = timezone.now()
    entries_this_month = LedgerEntry.objects.filter(
        customer__trader=trader,
        date__year=now.year,
        date__month=now.month,
    )
    recovered_this_month = entries_this_month.filter(entry_type='payment').aggregate(
        t=Sum('amount'))['t'] or 0
    credit_given_this_month = entries_this_month.filter(entry_type='credit').aggregate(
        t=Sum('amount'))['t'] or 0

    recent_transactions = LedgerEntry.objects.filter(
        customer__trader=trader
    ).select_related('customer').order_by('-date')[:7]

    return render(request, 'ledger/dashboard.html', {
        'trader': trader,
        'active_page': 'dashboard',
        'total_owed': total_owed,
        'customers_owing_count': customers_owing_count,
        'total_customers': customers.count(),
        'recovered_this_month': recovered_this_month,
        'credit_given_this_month': credit_given_this_month,
        'recent_transactions': recent_transactions,
        'biggest_debtors': biggest_debtors,
    })
    
@login_required
def customer_list_view(request):
    trader = request.user.traderprofile
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(trader=trader)
    if query:
        customers = customers.filter(name__icontains=query) | customers.filter(phone__icontains=query)
    return render(request, 'ledger/customer_list.html', {
        'customers': customers,
        'query': query,
        'trader': trader,
        'active_page': 'customers',
    })


@login_required
def customer_add_view(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.trader = request.user.traderprofile
            customer.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'ledger/customer_form.html', {
        'form': form,
        'title': 'Add Customer',
        'trader': request.user.traderprofile,
        'active_page': 'customers',
    })


@login_required
def customer_edit_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk, trader=request.user.traderprofile)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'ledger/customer_form.html', {
        'form': form,
        'title': 'Edit Customer',
        'trader': request.user.traderprofile,
        'active_page': 'customers',
    })


@login_required
def customer_delete_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk, trader=request.user.traderprofile)
    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')
    return render(request, 'ledger/customer_confirm_delete.html', {
        'customer': customer,
        'trader': request.user.traderprofile,
        'active_page': 'customers',
    })
    
@login_required
def transaction_add_view(request, entry_type):
    trader = request.user.traderprofile
    if entry_type not in ('credit', 'payment'):
        return redirect('dashboard')

    if request.method == 'POST':
        form = LedgerEntryForm(request.POST, trader=trader)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.entry_type = entry_type
            entry.save()
            return redirect('dashboard')
    else:
        form = LedgerEntryForm(trader=trader)

    return render(request, 'ledger/transaction_form.html', {
        'form': form,
        'entry_type': entry_type,
        'title': 'Record Credit' if entry_type == 'credit' else 'Record Payment',
        'trader': trader,
        'active_page': 'transactions',
    })

@login_required
def customer_detail_view(request, pk):
    trader = request.user.traderprofile
    customer = get_object_or_404(Customer, pk=pk, trader=trader)
    entries = customer.entries.order_by('-date')

    statement_url = request.build_absolute_uri(
        reverse('customer_statement', args=[customer.statement_token])
    )

    # Format phone for WhatsApp: strip spaces/dashes, convert leading 0 to Nigeria's 234
    digits = ''.join(filter(str.isdigit, customer.phone))
    if digits.startswith('0'):
        digits = '234' + digits[1:]
    whatsapp_phone = digits

    balance = customer.balance()
    if balance > 0:
        message = (
            f"Hello {customer.name}, this is a reminder from {trader.business_name}. "
            f"Your current balance is ₦{balance:,.0f}. "
            f"You can view your full statement here: {statement_url}"
        )
    else:
        message = (
            f"Hello {customer.name}, this is {trader.business_name}. "
            f"Your account is fully settled. Thank you!"
        )

    whatsapp_link = f"https://wa.me/{whatsapp_phone}?text={quote(message)}"

    return render(request, 'ledger/customer_detail.html', {
        'customer': customer,
        'entries': entries,
        'trader': trader,
        'active_page': 'customers',
        'statement_url': statement_url,
        'whatsapp_link': whatsapp_link,
    })
    
def customer_statement_view(request, token):
    customer = get_object_or_404(Customer, statement_token=token)
    entries = customer.entries.order_by('-date')

    return render(request, 'ledger/customer_statement.html', {
        'customer': customer,
        'entries': entries,
    })
    
@login_required
def monthly_summary_view(request):
    trader = request.user.traderprofile
    entries = LedgerEntry.objects.filter(customer__trader=trader)

    monthly = (
        entries
        .annotate(month=TruncMonth('date'))
        .values('month', 'entry_type')
        .annotate(total=Sum('amount'))
        .order_by('-month')
    )

    # Reshape into {month: {credit: x, payment: y}}
    summary = {}
    for row in monthly:
        month = row['month']
        summary.setdefault(month, {'credit': 0, 'payment': 0})
        summary[month][row['entry_type']] = row['total']

    summary_list = [
    {
        'month': month,
        'credit': data['credit'],
        'payment': data['payment'],
        'net': data['credit'] - data['payment'],
    }
    for month, data in sorted(summary.items(), reverse=True)
]

    return render(request, 'ledger/monthly_summary.html', {
        'trader': trader,
        'active_page': 'reports',
        'summary_list': summary_list,
    })
    
    
@login_required
def statement_directory_view(request):
    trader = request.user.traderprofile
    customers = Customer.objects.filter(trader=trader)

    customer_links = []
    for customer in customers:
        url = request.build_absolute_uri(
            reverse('customer_statement', args=[customer.statement_token])
        )
        customer_links.append({'customer': customer, 'url': url})

    return render(request, 'ledger/statement_directory.html', {
        'trader': trader,
        'active_page': 'statements',
        'customer_links': customer_links,
    })
    
def logout_view(request):
    logout(request)
    return redirect('login')