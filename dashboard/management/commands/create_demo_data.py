"""
Management command: create_demo_data

Seeds the database with realistic Thai print shop data so the dashboard
and all views have meaningful content to display.

Usage:
    python manage.py create_demo_data          # add demo data
    python manage.py create_demo_data --reset  # wipe jobs/customers first, then add
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with demo customers, jobs, payments, and documents"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing jobs, payments, and customers before seeding",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        admin = self._get_or_create_staff()
        customers = self._create_customers(admin)
        self._create_jobs(customers, admin)
        self.stdout.write(self.style.SUCCESS("Demo data created successfully."))

    # -------------------------------------------------------------------------

    def _reset(self):
        from documents.models import Document
        from jobs.models import Job
        from payments.models import Payment

        Payment.objects.all().delete()
        Document.objects.all().delete()
        Job.objects.all().delete()
        from customers.models import Customer
        Customer.objects.filter(name__startswith="[Demo]").delete()
        self.stdout.write("  Reset: cleared jobs, payments, documents, demo customers.")

    def _get_or_create_staff(self):
        """Return (or create) staff users for each role."""
        from accounts.models import Role

        users = {}
        specs = [
            ("owner", "สมศักดิ์", "เจ้าของ", Role.OWNER),
            ("counter1", "มาลี", "พนักงาน", Role.COUNTER),
            ("designer1", "อาทิตย์", "ออกแบบ", Role.DESIGNER),
            ("operator1", "สมหมาย", "ช่างพิมพ์", Role.OPERATOR),
        ]
        for username, first, last, role in specs:
            u, created = User.objects.get_or_create(
                username=username,
                defaults=dict(first_name=first, last_name=last, role=role),
            )
            if created:
                u.set_password("demo1234")
                u.save()
                self.stdout.write(f"  Created user: {username}")
            users[username] = u
        # fallback: use superuser as counter staff
        users.setdefault("counter1", User.objects.filter(is_superuser=True).first())
        return users

    def _create_customers(self, users):
        from customers.models import Customer, CustomerType

        walkin = CustomerType.objects.get(name__icontains="ทั่วไป")
        regular = CustomerType.objects.filter(name__icontains="ประจำ").first() or walkin
        corporate = CustomerType.objects.filter(name__icontains="นิติ").first() or walkin

        specs = [
            # (name, phone, type, is_corporate, tax_id)
            ("[Demo] บริษัท สยามเทค จำกัด",       "02-111-2345", corporate, True,  "0105560123456"),
            ("[Demo] ร้านกาแฟดอยช้าง",             "081-234-5678", regular,  False, ""),
            ("[Demo] โรงเรียนอนุบาลดาวทอง",        "02-555-6789", regular,  False, ""),
            ("[Demo] คุณสมหญิง รักดี",             "089-876-5432", walkin,   False, ""),
            ("[Demo] บริษัท แกรนด์ อีเวนท์ จำกัด", "02-888-9999", corporate, True,  "0105560234567"),
            ("[Demo] ร้านเสริมสวยนงนุช",           "085-111-2222", walkin,   False, ""),
            ("[Demo] สำนักงานกฎหมาย นิติธรรม",     "02-333-4444", regular,  False, ""),
        ]
        customers = []
        for name, phone, ctype, corp, tax in specs:
            c, _ = Customer.objects.get_or_create(
                name=name,
                defaults=dict(phone=phone, customer_type=ctype, is_corporate=corp, tax_id=tax),
            )
            customers.append(c)
        self.stdout.write(f"  Customers: {len(customers)}")
        return customers

    def _create_jobs(self, customers, users):
        from accounts.models import Role
        from jobs.models import Job, JobStatus
        from payments.models import Payment, PaymentMethod
        from production.models import ProductType

        counter = users.get("counter1") or User.objects.filter(is_superuser=True).first()
        designer = users.get("designer1") or counter
        operator = users.get("operator1") or counter  # noqa: F841

        pts = {pt.name: pt for pt in ProductType.objects.all()}

        def pt(name):
            # fuzzy match
            for k, v in pts.items():
                if name.lower() in k.lower():
                    return v
            return ProductType.objects.first()

        now = timezone.now()
        today = timezone.localdate()

        # Each tuple: (customer_idx, title, product_key, qty, w, h, price, deposit, status, days_ago, due_offset, designer_assign, notes)
        # days_ago = how many days ago the job was created
        # due_offset = due_date relative to today (+positive = future, -negative = overdue)
        job_specs = [
            # ---- COMPLETED + PAID this month (drive revenue) ----
            (0, "ป้ายสำนักงานชั้น 3",         "ป้ายไวนิล",   2,  200, 100, 3200, 1600, "completed", 14,  0, False),
            (0, "สติกเกอร์ติดรถยนต์",         "สติกเกอร์",   4,   80,  30, 1600,  800, "completed", 10,  0, True),
            (1, "นามบัตรร้านกาแฟ (500 ใบ)",   "นามบัตร",     5,    0,   0, 1250,    0, "completed",  7,  0, True),
            (2, "ใบปลิว A5 โรงเรียน",          "ใบปลิว",   2000,    0,   0, 6000, 3000, "completed",  5,  0, True),
            (6, "โบรชัวร์สำนักงานกฎหมาย",      "โบรชัวร์",  300,    0,   0, 2400, 1200, "completed",  3,  0, True),
            (4, "ป้ายผ้างานอีเวนท์ 3x2",       "ป้ายผ้า",     1,  300, 200, 5400, 2700, "completed",  6,  0, False),
            # ---- COMPLETED + PAID last month (don't count in this month revenue) ----
            (3, "สติกเกอร์ตกแต่งร้าน",        "สติกเกอร์",   3,   60,  40,  900,    0, "completed", 35,  0, True),
            (5, "นามบัตร 200 ใบ",              "นามบัตร",     2,    0,   0,  500,    0, "completed", 32,  0, True),
            # ---- READY (waiting for pickup) ----
            (0, "ป้ายไวนิลสำหรับงาน Expo",    "ป้ายไวนิล",   4,  120, 240, 8640, 4000, "ready",      2,  1, False),
            (3, "โปสเตอร์ A1 คอนเสิร์ต",      "พิมพ์ทั่วไป", 50,   0,   0,  750,    0, "ready",      3,  2, True),
            # ---- IN PRODUCTION ----
            (1, "ป้ายเมนูร้านกาแฟ",            "ป้ายไวนิล",   6,   60,  40, 2880, 1440, "printing",   1,  3, False),
            (4, "ป้ายนิทรรศการ 2x3",           "ป้ายผ้า",     3,  200, 300, 6480, 3000, "cutting",    2,  2, False),
            # ---- AWAITING APPROVAL (design review) ----
            (0, "โบรชัวร์บริษัท (ใหม่ปี 2568)", "โบรชัวร์",  500,    0,   0, 4000, 2000, "awaiting_approval", 3,  5, True),
            (2, "โปสเตอร์กิจกรรมโรงเรียน",      "พิมพ์ทั่วไป", 100,  0,   0, 2000, 1000, "awaiting_approval", 2,  4, True),
            # ---- DESIGNING ----
            (6, "นามบัตรทีมงาน (10 คน)",        "นามบัตร",    10,    0,   0, 2500, 1250, "designing",  1,  6, True),
            (5, "สติกเกอร์ฉลากสินค้า",          "สติกเกอร์",  50,   10,   5, 1500,  500, "designing",  1,  4, True),
            # ---- PENDING (new, unassigned) ----
            (3, "ป้ายหน้าร้านพิมพ์ใหม่",        "ป้ายไวนิล",   1,  300, 100, 2700,    0, "pending",    0,  7, False),
            (4, "ป้ายอะคริลิกโลโก้บริษัท",      "ป้ายอะคริล", 3,    0,   0, 2400, 1200, "pending",    0,  5, False),
            (1, "ใบปลิว Flyer ร้านกาแฟ",        "ใบปลิว",    1000,   0,   0, 3000,    0, "pending",    0,  3, False),
            # ---- OVERDUE: past due date, still pending/designing ----
            (5, "ป้ายโปรโมชันลดราคา",            "ป้ายไวนิล",   2,  100, 60, 1080,  540, "designing", 10, -3, True),
            (0, "สมุดโน้ตแจกพนักงาน 100 เล่ม",  "สมุดโน้ต",  100,   0,   0,12000, 6000, "pending",    5, -2, False),
        ]

        created_count = 0
        for spec in job_specs:
            (ci, title, prod_key, qty, w, h, price, deposit,
             target_status, days_ago, due_offset, assign_designer) = spec

            customer = customers[ci % len(customers)]
            product = pt(prod_key)
            created_at = now - timedelta(days=days_ago)
            due_date = today + timedelta(days=due_offset) if due_offset != 0 else None

            job = Job.objects.create(
                customer=customer,
                product_type=product,
                title=title,
                quantity=qty,
                width_cm=w or None,
                height_cm=h or None,
                quoted_price=Decimal(str(price)),
                deposit_amount=Decimal(str(deposit)),
                due_date=due_date,
                created_by=counter,
                assigned_designer=designer if assign_designer else None,
            )
            # Backdate created_at (can't set auto_now_add via create)
            Job.objects.filter(pk=job.pk).update(created_at=created_at, updated_at=created_at)
            job.refresh_from_db()

            # Drive through status transitions
            self._advance_to(job, target_status, counter, designer, created_at)

            # Add payments for completed / ready / in-production jobs
            self._add_payments(job, target_status, deposit, price, counter, created_at)

            created_count += 1

        self.stdout.write(f"  Jobs: {created_count} created")

    def _advance_to(self, job, target_status, counter, designer, base_time):
        """Walk the job through status transitions to reach target_status."""
        from jobs.models import JobStatus, ALLOWED_TRANSITIONS

        path_map = {
            "designing":          ["designing"],
            "awaiting_approval":  ["designing", "awaiting_approval"],
            "revision":           ["designing", "awaiting_approval", "revision"],
            "approved":           ["designing", "awaiting_approval", "approved"],
            "printing":           ["printing"],
            "cutting":            ["printing", "cutting"],
            "laminating":         ["printing", "cutting", "laminating"],
            "ready":              ["printing", "ready"],
            "completed":          ["printing", "ready", "completed"],
            "cancelled":          ["cancelled"],
        }
        steps = path_map.get(target_status, [])

        for i, step in enumerate(steps):
            by = designer if step in ("designing", "awaiting_approval", "revision", "approved") else counter
            try:
                job.transition_to(step, changed_by=by, note="")
                # backdate the history entry
                from jobs.models import JobStatusHistory
                JobStatusHistory.objects.filter(job=job, to_status=step).update(
                    changed_at=base_time + timedelta(hours=i * 4 + random.randint(1, 3))
                )
            except ValueError:
                pass  # already at or past this step

    def _add_payments(self, job, target_status, deposit, price, counter, base_time):
        from payments.models import Payment, PaymentMethod

        now = timezone.now()

        if target_status == "completed":
            # Full payment
            Payment.objects.create(
                job=job,
                amount=Decimal(str(price)),
                method=random.choice([PaymentMethod.CASH, PaymentMethod.PROMPTPAY, PaymentMethod.BANK_TRANSFER]),
                received_by=counter,
                notes="ชำระครบ",
            )
            Payment.objects.filter(job=job).update(received_at=base_time + timedelta(days=1))

        elif target_status in ("ready", "printing", "cutting"):
            # Deposit only
            if deposit > 0:
                Payment.objects.create(
                    job=job,
                    amount=Decimal(str(deposit)),
                    method=PaymentMethod.CASH,
                    is_deposit=True,
                    received_by=counter,
                    notes="มัดจำ",
                )
                Payment.objects.filter(job=job).update(received_at=base_time + timedelta(hours=1))
