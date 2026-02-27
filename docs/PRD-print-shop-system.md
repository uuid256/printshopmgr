# Product Requirements Document (PRD)
# ระบบจัดการร้านป้ายและสิ่งพิมพ์ — Print Shop Management System

**Product:** เจ๊าะแจ๊ะป้ายสวย — Sign & Print Shop Management
**Version:** 1.0
**Date:** February 26, 2026
**Author:** Product Owner
**Status:** Ready for Development

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Goals & Success Metrics](#2-goals--success-metrics)
3. [User Roles & Permissions](#3-user-roles--permissions)
4. [Feature Specifications](#4-feature-specifications)
5. [Job Status Flow](#5-job-status-flow)
6. [Data Model](#6-data-model)
7. [Business Rules](#7-business-rules)
8. [Integration Requirements](#8-integration-requirements)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Wireframe Reference](#10-wireframe-reference)
11. [Phased Delivery Plan](#11-phased-delivery-plan)
12. [Glossary](#12-glossary)

---

## 1. Product Overview

### 1.1 What

A web-based management system for a Thai print/sign shop that handles the complete lifecycle from customer order → graphic design → customer approval → production → payment → delivery.

### 1.2 Why

Current pain points:
- 1,361 outstanding payment records with no aging visibility
- Staff spends 2+ hours/day answering "is my job ready?" inquiries
- No visibility into production bottlenecks
- No formal design approval — leads to costly reprints
- Manual price calculation and document generation
- No connection between LINE orders and job management

### 1.3 Who

Primary users: Counter Staff, Graphic Designers, Production Operators, Accountant, Shop Owner. Secondary users: Customers (via LINE and web tracking page).

### 1.4 Current System

Running at `192.168.1.53` with existing data: 7,396 completed jobs, 259 customers, 14 users, 23 product categories, 13 customer types.

---

## 2. Goals & Success Metrics

| Goal | Metric | Target |
|---|---|---|
| Reduce "is my job ready?" calls | Customer inquiries per day | -70% within 3 months |
| Improve payment collection | Outstanding payments aging > 30 days | -40% within 6 months |
| Reduce reprints from miscommunication | Revision rate after production | < 5% |
| Increase production visibility | Jobs with accurate status | 100% |
| Speed up order intake | Average time to create a job | < 3 minutes |
| Owner visibility | Time to get business overview | < 30 seconds (dashboard) |

---

## 3. User Roles & Permissions

### 3.1 Role Definitions

**R1: เจ้าของร้าน / Owner (Admin)**
- Full system access
- Business reports, user management, system settings
- Typical count: 1

**R2: พนักงานหน้าร้าน / Counter Staff**
- Create/edit jobs, manage customers, receive payments, search job status
- Cannot access: financial reports, user management, system settings
- Typical count: 2-3

**R3: กราฟิกดีไซเนอร์ / Graphic Designer**
- Design queue, upload artwork, submit for approval, view job specs
- Cannot access: pricing, payments, financial data
- Typical count: 2-4

**R4: ช่างผลิต / Production Operator**
- Production queue, mark job progress, log material usage
- Cannot access: customer data, pricing, financial reports
- Typical count: 2-4

**R5: บัญชี / Accountant**
- Payment records, invoices, receipts, tax reports, outstanding balances
- Cannot access: design files, production controls, system settings
- Typical count: 1

**R6: ลูกค้า / Customer (External — no login)**
- View own job status via unique URL
- Approve/reject design proofs
- No system login required

### 3.2 Permission Matrix

| Feature | R1 Owner | R2 Counter | R3 Designer | R4 Production | R5 Accountant |
|---|---|---|---|---|---|
| Dashboard (full) | ✅ | — | — | — | — |
| Dashboard (own queue) | — | ✅ | ✅ | ✅ | ✅ |
| Create Job | ✅ | ✅ | — | — | — |
| Edit Job | ✅ | ✅ | Own only | Own only | — |
| Delete/Cancel Job | ✅ | — | — | — | — |
| View All Jobs | ✅ | ✅ | View only | View only | View only |
| Customer CRUD | ✅ | ✅ | — | — | View only |
| Design Queue | ✅ | View only | ✅ | View only | — |
| Upload Artwork | ✅ | — | ✅ | — | — |
| Send for Approval | ✅ | — | ✅ | — | — |
| Production Queue | ✅ | View only | View only | ✅ | — |
| Update Production Status | ✅ | — | — | ✅ | — |
| Receive Payment | ✅ | ✅ | — | — | ✅ |
| Generate Quotation | ✅ | ✅ | — | — | ✅ |
| Generate Tax Invoice | ✅ | ✅ | — | — | ✅ |
| Generate Receipt | ✅ | ✅ | — | — | ✅ |
| Generate Statement | ✅ | — | — | — | ✅ |
| Financial Reports | ✅ | — | — | — | ✅ |
| Tax Reports | ✅ | — | — | — | ✅ |
| Outstanding Payments | ✅ | View only | — | — | ✅ |
| Inventory Management | ✅ | — | — | ✅ | ✅ |
| User Management | ✅ | — | — | — | — |
| System Settings | ✅ | — | — | — | — |
| Pricing Rules | ✅ | — | — | — | — |

### 3.3 Multi-role Support

A single user may hold multiple roles (e.g., Owner who also does accounting). The system must support assigning multiple roles per user.

---

## 4. Feature Specifications

### 4.1 Job Management (Module: JOB)

**JOB-001: Create Job**
- Actor: Counter Staff, Owner
- Wizard flow: Select Customer → Job Details → Pricing → Payment → Confirmation
- Required fields: customer, job name, product type, size, quantity, material, due date
- Optional fields: artwork file, notes, PO number, channel source
- Auto-assign job number (sequential, never reused)
- Auto-suggest due date based on current queue depth

**JOB-002: Search & View Job**
- Search by: job number, customer name, job name, phone number
- Result shows: status, storage location, payment balance, timeline
- Quick actions: receive payment, view detail, print job slip

**JOB-003: Job Status Update**
- Each role can update to next valid status (see Section 5)
- Status change triggers: notification, timestamp logging, assigned-user logging
- Status change via: web UI button, QR code scan (mobile)

**JOB-004: Job QR Code**
- Generate QR code per job containing job URL
- Printable on job slip (attached to physical job folder)
- Scanning opens mobile status update page

**JOB-005: Duplicate/Reorder Job**
- Create new job by copying previous job details
- Pre-fill all fields, allow editing before save
- Link to original job for reference

**JOB-006: Cancel Job**
- Actor: Owner only
- Requires reason
- Refund handling if deposit was paid
- Status → ยกเลิก (Cancelled)

### 4.2 Customer Management (Module: CUST)

**CUST-001: Customer CRUD**
- Types: บุคคลทั่วไป (Individual), องค์กร/บริษัท (Corporate)
- Fields: name, phone (required), LINE ID, email, address, tax ID, branch number, customer type, credit terms, credit limit
- Quick-add modal for walk-in customers (minimal fields)

**CUST-002: Customer Profile**
- Job history with all past orders
- Total spending, average order value
- Outstanding balance
- Payment history
- Documents issued

**CUST-003: Corporate Customer**
- Credit terms: 15/30/60/90 days
- Credit limit with usage tracking
- PO number support
- Auto-generate monthly statements
- Tax invoice auto-enabled

**CUST-004: Walk-in Customer**
- System default "ลูกค้าทั่วไป" customer for anonymous orders
- Can upgrade to named customer at any time

### 4.3 Design Workflow (Module: DESIGN)

**DESIGN-001: Design Queue (Kanban)**
- Columns: รอออกแบบ → กำลังทำ → รออนุมัติ → แก้ไข
- Drag-drop between columns to update status
- Cards show: job type, name, deadline countdown, priority, assigned designer
- Filter by: assigned designer, priority, product type
- Sort by: deadline, priority, created date

**DESIGN-002: Design Workspace**
- Split view: job specs (left) + files (right)
- Customer reference files viewable
- Designer notes field (visible to production)
- Open file in native app (Finder/Explorer)

**DESIGN-003: Upload Proof**
- Two file slots: original working file (.AI/.PSD/.PDF) + proof image (.JPG/.PNG/.PDF)
- Auto-version: v1, v2, v3...
- Proof preview before sending
- Designer note to customer

**DESIGN-004: Customer Approval**
- Triggered by designer clicking "ส่งอนุมัติ"
- Sends LINE notification with proof image
- Customer approves or requests revision via: LINE buttons, web tracking page
- Approval updates job status automatically
- Revision captures: customer text, annotated images

**DESIGN-005: Version History**
- Track all design versions
- Side-by-side comparison
- Full audit trail: who uploaded, when, customer response

### 4.4 Production Workflow (Module: PROD)

**PROD-001: Production Queue**
- List view sorted by: priority (URGENT first), then due date
- Large clear job cards with: size, material, machine, quantity
- Filter by: machine type (InkJet, Laser, Offset), priority

**PROD-002: Production Status Update**
- Button-based: เริ่มผลิต → กำลังพิมพ์ → ตัด/เก็บงาน → QC → รอรับงาน
- Mobile-friendly: large tap targets
- QR scan: scan job QR → one-tap status update
- Problem reporting: "มีปัญหา" button → alert to owner

**PROD-003: Printable Job Card**
- A5 format, printable
- Includes: QR code, job specs, material, special instructions, sign-off checkboxes
- Physical document travels with the job

**PROD-004: Material Usage Logging**
- Log material used per job (type, quantity)
- Links to inventory tracking
- Cost calculation support

### 4.5 Billing & Payments (Module: BILL)

**BILL-001: Auto-Pricing Engine**
- Calculate price based on: product type, material, size, quantity
- Configurable pricing rules per product category
- Support for: per-piece pricing, per-sqm pricing, flat rate
- Design fee (configurable: included, separate, waived)
- Finishing fee (cut, laminate, frame — per type)
- Discount: fixed amount (฿) or percentage (%)
- VAT 7% auto-calculation
- Staff can override auto-calculated price

**BILL-002: Payment Recording**
- Payment types: ชำระเต็มจำนวน (Full), มัดจำ (Deposit), วางบิล/เครดิต (Credit)
- Payment methods: เงินสด (Cash), พร้อมเพย์/PromptPay (with QR generation), โอนธนาคาร (Bank Transfer), เช็ค (Cheque), บัตรเครดิต (Credit Card)
- Partial payment support (multiple payments per job)
- Slip attachment (photo upload)
- Default deposit: 50% (configurable)

**BILL-003: PromptPay QR Generation**
- Generate QR code with exact payment amount
- Display shop name and payment details
- Works for both deposit and final payment

**BILL-004: Document Generation**

All documents must include:
- Sequential running number (no gaps — Thai legal requirement)
- Shop tax ID, name, address
- Date
- VAT breakdown when applicable

| Document | Thai Name | When Generated |
|---|---|---|
| Quotation | ใบเสนอราคา | Before job creation (optional) |
| Invoice | ใบแจ้งหนี้ / ใบวางบิล | Job complete, requesting payment |
| Tax Invoice | ใบกำกับภาษี | Upon payment (if customer requests) |
| Receipt | ใบเสร็จรับเงิน | Upon payment |
| Combined Tax Invoice/Receipt | ใบกำกับภาษี/ใบเสร็จรับเงิน | Upon payment (most common) |
| Monthly Statement | ใบวางบิลรายเดือน | End of month for credit customers |
| Delivery Note | ใบส่งของ | Job handover |

**BILL-005: Tax Invoice Requirements**
- Customer tax ID (13-digit Thai format: X-XXXX-XXXXX-XX-X)
- Branch number (00000 = สำนักงานใหญ่)
- Itemized breakdown
- VAT 7% separated
- Thai baht text (ตัวอักษร) auto-generated from amount
- Must follow Thai Revenue Department format

**BILL-006: Withholding Tax (WHT)**
- Corporate customers may deduct WHT before payment
- Common rates: 2% (ค่าโฆษณา), 3% (ค่าจ้างทำของ)
- WHT calculated from pre-VAT amount
- Attach WHT certificate (หนังสือรับรองการหัก ณ ที่จ่าย)
- Record: full invoice amount, WHT deduction, net received

**BILL-007: Outstanding Payment Management**
- Aging report: ยังไม่ถึงกำหนด, 1-30 days, 31-60 days, 61-90 days, 90+ days
- Per-customer breakdown
- Batch reminder sending (LINE/SMS)
- Credit limit enforcement (warn/block new orders when over limit)
- Export to Excel

**BILL-008: Monthly Statement Generation (Credit Customers)**
- Auto-group all credit jobs for billing period
- Itemized with all job details
- Attach related tax invoices
- Send via: print, email, LINE
- Track statement status: sent, acknowledged, paid

### 4.6 Tax Reports (Module: TAX)

**TAX-001: Output Tax Report (รายงานภาษีขาย)**
- Monthly report of all tax invoices issued
- Columns: date, invoice number, customer name, pre-VAT amount, VAT amount
- Sequential by invoice number
- Summary totals
- Format compatible with ภ.พ.30 filing

**TAX-002: Input Tax Report (รายงานภาษีซื้อ)**
- Monthly report of all tax invoices received from suppliers
- Manual entry of supplier invoices
- Summary totals

**TAX-003: VAT Summary (สรุป ภ.พ.30)**
- Output Tax - Input Tax = Net VAT payable
- Filing deadline reminder (15th of following month)

**TAX-004: WHT Report**
- Summary of all WHT certificates received
- For annual tax filing

### 4.7 Reports & Dashboard (Module: RPT)

**RPT-001: Owner Dashboard**
- Revenue: today / this week / this month with comparison to previous period
- Revenue trend chart (30-day sparkline)
- Pipeline summary: count per status, overdue alerts
- Critical alerts: overdue jobs, overdue payments, low stock
- Today's summary: new jobs, completed, delivered

**RPT-002: Pipeline Kanban (All Jobs)**
- Full Kanban view: all active jobs across all statuses
- Filter by: staff, priority, product type, date range
- Owner can reassign and change priority
- Summary: total active, overdue count, average completion time

**RPT-003: Revenue Report**
- By period: daily, weekly, monthly, annual
- By product type: vinyl, sticker, sign, business card, etc.
- By channel: walk-in, LINE, Facebook, phone, corporate
- By payment method: cash, transfer, PromptPay, credit
- Top customers ranking
- Compare with previous period (% change)

**RPT-004: Staff Performance**
- Designer: jobs completed, average design time, revision rate
- Production: jobs completed, average production time, issue rate, waste rate
- Counter: jobs created, payments collected, outstanding per staff
- Customer satisfaction score per staff

**RPT-005: Daily Summary (Auto-generated)**
- Revenue by payment method
- Jobs: new, completed, delivered, cancelled
- Outstanding items: overdue jobs, overdue payments
- Material alerts
- Comparison with previous day/week
- Auto-send to owner via LINE at closing time

### 4.8 Inventory Management (Module: INV)

**INV-001: Material Tracking**
- Material categories: ink, vinyl rolls, paper, card stock, lamination, frames
- Stock quantity with unit (rolls, sheets, liters, pieces)
- Low-stock threshold per material
- Alert when below threshold

**INV-002: Usage Logging**
- Log material consumed per job
- Track waste/spoilage separately
- Cost per job calculation

**INV-003: Stock Alerts**
- Notification to owner and production when stock is low
- Estimated days until depletion (based on usage rate)

### 4.9 Notification System (Module: NOTIF)

**NOTIF-001: LINE Notifications to Customer**

| Trigger | Message |
|---|---|
| Job created | Order confirmed + job number + estimated completion |
| Design proof ready | Proof image + approve/reject buttons |
| Revision received | Acknowledgment + estimated time |
| Job ready for pickup | Notification + payment info if balance due |
| Job shipped | Tracking number + courier + estimated delivery |
| Payment reminder | Outstanding amount + payment QR |
| Post-delivery | Thank you + rating link + discount code |

**NOTIF-002: Internal Notifications**

| Trigger | Notify Who |
|---|---|
| New job created | Assigned designer |
| Customer approved design | Production queue + counter staff |
| Customer requested revision | Designer |
| Job completed production | Counter staff |
| Problem in production | Owner + counter staff |
| Payment received | Accountant |
| Payment overdue (30/60/90 days) | Owner + accountant |
| Low stock alert | Owner + production |
| Job overdue | Owner |

**NOTIF-003: Notification Center**
- In-app notification bell with badge count
- Color-coded: 🔴 critical, 🟡 warning, 🔵 info, 🟢 positive
- Click to navigate to relevant screen
- Mark as read / mark all read

### 4.10 Customer-Facing Features (Module: CFACE)

**CFACE-001: Job Tracking Page (Public)**
- Accessed via unique URL (no login)
- Shows: job details, status timeline, payment summary
- Design proof with approve/reject (when in approval status)
- Deep-link back to LINE for questions
- Mobile-first responsive design

**CFACE-002: Satisfaction Survey**
- Auto-sent 1 hour after pickup/delivery
- 3 categories: quality, speed, service (5-star each)
- Optional text feedback
- Unique discount code per job for next order

---

## 5. Job Status Flow

### 5.1 Status Definitions

| Code | Thai | English | Color | Set By |
|---|---|---|---|---|
| RECEIVED | รับงาน | Order Received | ⚪ Gray | Counter Staff |
| DEPOSIT_PENDING | รอชำระมัดจำ | Awaiting Deposit | 🟠 Orange | System (auto) |
| DESIGNING | กำลังออกแบบ | Designing | 🔵 Blue | Designer |
| APPROVAL_PENDING | รอลูกค้าอนุมัติ | Awaiting Approval | 🟡 Yellow | Designer |
| REVISION | แก้ไข | Revision | 🟣 Purple | Customer/System |
| PRODUCTION_QUEUE | รอคิวผลิต | Production Queue | ⚪ Gray | System (auto) |
| PRINTING | กำลังผลิต | Printing | 🔵 Blue | Production |
| FINISHING | ตัด/เก็บงาน | Finishing | 🔵 Blue | Production |
| QC | ตรวจคุณภาพ | Quality Check | 🟡 Yellow | Production |
| READY_PICKUP | รอรับงาน | Ready for Pickup | 🟢 Green | Production |
| DELIVERING | จัดส่ง | Delivering | 🔵 Blue | Counter Staff |
| COMPLETED | เสร็จสมบูรณ์ | Completed | ✅ Green | Counter Staff |
| CANCELLED | ยกเลิก | Cancelled | 🔴 Red | Owner |

### 5.2 Valid Transitions

```
RECEIVED → DEPOSIT_PENDING (if deposit required)
RECEIVED → DESIGNING (if no deposit or deposit paid)
DEPOSIT_PENDING → DESIGNING (after deposit received)
DESIGNING → APPROVAL_PENDING
APPROVAL_PENDING → PRODUCTION_QUEUE (customer approved)
APPROVAL_PENDING → REVISION (customer requests changes)
REVISION → DESIGNING (designer starts revision)
PRODUCTION_QUEUE → PRINTING
PRINTING → FINISHING
FINISHING → QC (optional — can skip)
FINISHING → READY_PICKUP (if no QC)
QC → READY_PICKUP (passed)
QC → PRINTING (failed — reprint)
READY_PICKUP → DELIVERING (if delivery)
READY_PICKUP → COMPLETED (if pickup + paid)
DELIVERING → COMPLETED (delivered + paid)
Any status → CANCELLED (Owner only)
```

### 5.3 Status Change Logging

Every status change must log:
- Previous status
- New status
- Changed by (user ID)
- Timestamp
- Notes (optional)

---

## 6. Data Model

### 6.1 Core Entities

**users**
```
id, username, password_hash, display_name, email, phone,
roles[] (many-to-many), is_active, created_at, updated_at
```

**customers**
```
id, name, type (individual/corporate), phone, line_id, email,
address, tax_id, branch_number, customer_type_id,
credit_terms_days, credit_limit, notes,
created_at, updated_at
```

**jobs**
```
id, job_number (display), customer_id, job_name, description,
product_type_id, size_width, size_height, size_unit,
quantity, material_id, machine_type,
channel (walkin/line/facebook/phone/web),
status, priority (normal/urgent/rush),
assigned_designer_id, assigned_operator_id,
due_date, notes, po_number,
total_price, discount_amount, discount_type (fixed/percent),
pre_vat_amount, vat_amount, total_with_vat,
delivery_method (pickup/delivery), delivery_address,
storage_location,
created_by, created_at, updated_at
```

**job_status_history**
```
id, job_id, previous_status, new_status,
changed_by, notes, created_at
```

**job_files**
```
id, job_id, file_type (customer_artwork/design_proof/working_file),
file_path, file_name, file_size, mime_type,
version, uploaded_by, created_at
```

**job_approvals**
```
id, job_id, version, proof_file_id,
designer_note, customer_response (approved/revision),
customer_note, customer_annotation_file_id,
responded_at, created_at
```

**payments**
```
id, job_id, amount, payment_type (full/deposit/balance/credit),
payment_method (cash/promptpay/transfer/cheque/card),
bank_account_id, reference_number, slip_file_path,
wht_rate, wht_amount, net_received,
wht_certificate_file_path,
received_by, created_at
```

**documents**
```
id, job_id, customer_id, document_type
(quotation/invoice/tax_invoice/receipt/combined/statement/delivery_note),
document_number (sequential), date_issued,
pre_vat_amount, vat_amount, total_amount,
pdf_file_path, sent_via (print/email/line),
created_by, created_at
```

**document_items**
```
id, document_id, description, quantity, unit_price, amount
```

**materials**
```
id, name, category, unit, current_stock,
low_stock_threshold, cost_per_unit,
created_at, updated_at
```

**material_usage**
```
id, job_id, material_id, quantity_used,
waste_quantity, logged_by, created_at
```

**product_types**
```
id, name, base_price_per_unit, price_unit (piece/sqm/sqcm),
design_fee, default_material_id,
created_at, updated_at
```

**customer_types**
```
id, name, discount_rate, created_at
```

**bank_accounts**
```
id, bank_name, account_number, account_name,
promptpay_id, is_active
```

**notifications**
```
id, user_id (null for customer notifications),
customer_id (null for internal),
type (line/internal), channel,
title, message, reference_type, reference_id,
is_read, sent_at, created_at
```

**settings**
```
id, key, value, description
```

### 6.2 Key Indexes

- jobs: status, customer_id, due_date, created_at, assigned_designer_id, assigned_operator_id
- payments: job_id, created_at, payment_method
- documents: document_type, document_number, customer_id, created_at
- job_status_history: job_id, created_at
- notifications: user_id + is_read, customer_id

---

## 7. Business Rules

### 7.1 Job Rules

| Rule ID | Rule |
|---|---|
| JR-001 | Job number is auto-generated, sequential, never reused or recycled |
| JR-002 | Job cannot move backward in status flow except: APPROVAL_PENDING → REVISION → DESIGNING |
| JR-003 | Job cannot be deleted, only cancelled (with reason) |
| JR-004 | Due date must be at least 1 business day from creation |
| JR-005 | Only Owner can cancel a job |
| JR-006 | Cancelled jobs with payments must create refund record |
| JR-007 | Job cannot move to COMPLETED if outstanding balance > 0 (unless credit terms) |

### 7.2 Payment Rules

| Rule ID | Rule |
|---|---|
| PR-001 | Deposit default is 50% of total (configurable per customer type) |
| PR-002 | Credit terms only available for customers with customer.credit_terms_days > 0 |
| PR-003 | System warns when credit customer exceeds credit limit (does not block) |
| PR-004 | WHT is calculated on pre-VAT amount, not total |
| PR-005 | Payment slip attachment required for bank transfer and PromptPay |
| PR-006 | Cash payments do not require slip |

### 7.3 Document Rules

| Rule ID | Rule |
|---|---|
| DR-001 | Document numbers are sequential with no gaps (Thai legal requirement) |
| DR-002 | Document number format: {TYPE}-{YEAR}-{SEQUENCE} e.g., TX-2567-00001 |
| DR-003 | Tax invoice requires customer tax ID and branch number |
| DR-004 | Documents cannot be edited after issuance — issue credit note instead |
| DR-005 | Thai baht text (ตัวอักษร) must be auto-generated on all financial documents |
| DR-006 | All amounts shown with 2 decimal places |

### 7.4 VAT Rules

| Rule ID | Rule |
|---|---|
| VR-001 | VAT rate is 7% (configurable for future changes) |
| VR-002 | VAT calculated: total_with_vat = pre_vat_amount × 1.07 |
| VR-003 | When customer gives total amount, calculate backward: pre_vat = total / 1.07 |
| VR-004 | Monthly VAT filing deadline: 15th of following month |

### 7.5 Notification Rules

| Rule ID | Rule |
|---|---|
| NR-001 | Customer LINE notifications sent automatically on status change |
| NR-002 | Satisfaction survey sent 1 hour after COMPLETED status |
| NR-003 | Payment reminder sent at: 7 days before due, on due date, 7/30/60/90 days after due |
| NR-004 | Overdue job alert to owner when job exceeds due date by 1 day |
| NR-005 | Low stock alert when material drops below threshold |

---

## 8. Integration Requirements

### 8.1 LINE Messaging API

- **Purpose:** Customer notifications, design approval, payment reminders
- **Type:** LINE Official Account (Messaging API)
- **Features needed:** Push messages, Flex Messages (for rich cards), Rich Menu, LIFF (for approval page)
- **Rate limits:** Respect LINE message quota

### 8.2 PromptPay QR

- **Purpose:** Generate payment QR codes
- **Standard:** EMVCo QR Code for PromptPay
- **Data:** Recipient ID (phone/tax ID), amount, reference
- **Library:** Generate QR client-side or server-side

### 8.3 Accounting Software Export (Phase 2+)

- **Target systems:** PEAK Account, FlowAccount, or generic CSV export
- **Data:** Monthly sales, purchase invoices, payment records
- **Format:** CSV with Thai headers compatible with target system

### 8.4 Shipping Tracking (Phase 3+)

- **Carriers:** Kerry Express, Flash Express, Thailand Post
- **Data:** Tracking number, estimated delivery
- **Integration:** Manual entry initially, API integration later

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Requirement | Target |
|---|---|
| Page load time | < 2 seconds |
| Search response | < 1 second |
| Dashboard load | < 3 seconds |
| Concurrent users | 15+ simultaneous |
| Report generation | < 5 seconds |

### 9.2 Compatibility

| Platform | Requirement |
|---|---|
| Desktop browser | Chrome, Edge (latest 2 versions) |
| Tablet | iPad Safari, Android Chrome |
| Mobile | Responsive web (not native app) |
| Printer | Thermal receipt printer, A4/A5 laser/inkjet |

### 9.3 Localization

- Primary language: Thai
- Secondary language: English (for some labels)
- Date format: Thai Buddhist Era (พ.ศ.) and CE supported
- Currency: Thai Baht (฿) with 2 decimal places
- Number format: comma separators (1,000,000.00)

### 9.4 Security

- Role-based access control (RBAC)
- Password hashing (bcrypt)
- Session management with timeout
- Audit trail on all status changes and payments
- HTTPS (when deployed beyond local network)

### 9.5 Data

- Database backup: daily automated
- File storage backup: daily automated
- Data retention: minimum 7 years (Thai tax law)
- Upload file size limit: 50MB per file

---

## 10. Wireframe Reference

Detailed ASCII wireframes are provided in separate files:

| File | Journey | Screens |
|---|---|---|
| `01-walkin-new-order.md` | Walk-in customer places order | 7 screens: dashboard, customer select, job details, pricing, payment, confirmation, PromptPay QR, mobile view |
| `02-design-approval-production.md` | Design → approval → production | 9 screens: design Kanban, workspace, upload proof, LINE approval, revision view, production queue, job card, QR scan |
| `03-pickup-final-payment.md` | Customer picks up and pays | 6 screens: job search, payment, tax invoice, confirmation, receipt preview, satisfaction survey |
| `04-corporate-monthly-billing.md` | Corporate monthly billing | 6 screens: credit job creation, accountant dashboard, statement generation, aging report, WHT payment, tax report |
| `05-line-order-remote.md` | Remote order via LINE | 5 screens: LINE chat flow, staff order creation, customer tracking page, delivery form, delivery notification |
| `06-owner-daily-operations.md` | Owner daily management | 7 screens: morning dashboard, pipeline Kanban, revenue report, staff performance, daily summary, mobile view, notifications |

---

## 11. Phased Delivery Plan

> **Implementation note:** The delivery was grouped into 4 implementation phases that do not map 1:1 to the PRD phases below. The tables are updated with ✅ (built), ⚠️ (partial), and — (not yet built) to reflect the current state of the codebase.

### Phase 1: Core Foundation

**Goal:** Replace basic job management with proper status tracking

| Feature | Priority | Built? |
|---|---|---|
| User authentication + RBAC (5 staff roles + customer external) | P0 | ✅ |
| Job CRUD with 12-status flow + transition enforcement | P0 | ✅ |
| Job search / list / filter | P0 | ⚠️ basic list; no full-text search |
| Customer CRUD (individual + corporate) with live autocomplete | P0 | ✅ |
| Job status timeline view (status history) | P0 | ✅ |
| Job QR code generation (printable job slip) | P1 | — |
| Mobile-responsive layout (Tailwind) | P0 | ✅ |
| Database migration from existing system | P0 | — (fresh start) |

### Phase 2: Billing & Documents

**Goal:** Proper financial tracking and Thai tax document generation

| Feature | Priority | Built? |
|---|---|---|
| Pricing fields per job (quoted price, deposit, discount) | P0 | ✅ |
| Payment recording — full, deposit, WHT; PromptPay QR | P0 | ✅ |
| Quotation PDF (WeasyPrint, Buddhist Era dates, baht text) | P1 | ✅ |
| Tax Invoice PDF (Thai Revenue Dept compliant) | P0 | ✅ |
| Receipt PDF | P0 | ✅ |
| Credit Note PDF | P1 | ✅ |
| Outstanding payment list + aging report | P0 | ✅ |
| VAT report — output tax (ภ.พ.30 compatible) | P0 | ✅ |
| Monthly statement generation | P1 | — |
| Thai baht text (ตัวอักษร) converter | P0 | ✅ |

### Phase 3: Communication

**Goal:** Automated customer communication via LINE

| Feature | Priority | Built? |
|---|---|---|
| LINE OA integration (push messages via Messaging API) | P0 | ✅ |
| Auto-notification on status change | P0 | ✅ |
| Design proof upload + approval via LINE / public page | P0 | ✅ |
| Customer tracking page (public UUID URL, no login) | P0 | ✅ |
| Payment reminder — auto-scheduled Celery task | P1 | ✅ |
| Approval reminder — auto-scheduled Celery task | P1 | ✅ |
| Daily summary — auto-scheduled to owner (LINE + email) | P1 | ✅ |
| Low-stock material alert — auto-scheduled Celery task | P1 | ✅ |
| Satisfaction survey via LINE | P2 | — |
| Internal in-app notification center | P1 | — |

### Phase 4: Intelligence

**Goal:** Owner gets full business visibility and automation controls

| Feature | Priority | Built? |
|---|---|---|
| Owner dashboard (revenue, pipeline, overdue alerts) | P0 | ✅ |
| Designer Kanban (drag-drop via Sortable.js + HTMX) | P1 | ✅ |
| Revenue reports (by period, product, channel) | P0 | — |
| Staff performance dashboard | P2 | — |
| Tax reports — output VAT (ภ.พ.30) | P0 | ✅ |
| Celery Beat scheduler (django-celery-beat, DB scheduler) | P1 | ✅ |
| Notification settings page — email/LINE kill switches, thresholds | P1 | ✅ |
| LINE Login OAuth for staff accounts | P1 | ✅ |
| Export to Excel | P1 | — |

### Remaining / Future Work

| Feature | Priority |
|---|---|
| Job QR code → printable job slip (A5) | P1 |
| Full-text job search | P1 |
| Monthly statement generation for credit customers | P1 |
| Revenue report (by period, product type, channel) | P0 |
| Staff performance report | P2 |
| Satisfaction survey via LINE post-completion | P2 |
| In-app notification center (bell icon) | P1 |
| Accounting export (CSV for PEAK / FlowAccount) | P2 |
| Export to Excel (aging, payments, VAT) | P1 |
| Reorder from past job | P1 |

---

## 12. Glossary

| Thai Term | English | Description |
|---|---|---|
| ใบเสนอราคา | Quotation | Price quote before job creation |
| ใบแจ้งหนี้ / ใบวางบิล | Invoice | Bill requesting payment |
| ใบกำกับภาษี | Tax Invoice | VAT-registered invoice (legal document) |
| ใบเสร็จรับเงิน | Receipt | Proof of payment received |
| ใบส่งของ | Delivery Note | Proof of goods delivered |
| มัดจำ | Deposit | Advance payment before production |
| ค้างชำระ | Outstanding | Unpaid balance |
| วางบิล | Billing (credit) | Invoice now, pay later |
| ภาษีมูลค่าเพิ่ม (VAT) | Value Added Tax | 7% tax on goods and services |
| ภาษีหัก ณ ที่จ่าย (WHT) | Withholding Tax | Tax deducted by payer (2-3%) |
| หนังสือรับรองหัก ณ ที่จ่าย | WHT Certificate | Document proving WHT deduction |
| ภ.พ.30 | VAT Return Form | Monthly VAT filing to Revenue Department |
| เลขผู้เสียภาษี | Tax ID | 13-digit Thai tax identification number |
| สำนักงานใหญ่ | Head Office | Branch code: 00000 |
| พ.ศ. | Buddhist Era | Thai calendar year (CE + 543) |
| ไวนิล | Vinyl Banner | Large format printed banner |
| สติกเกอร์ | Sticker | Adhesive printed labels |
| ป้ายไฟ | Illuminated Sign | Backlit sign board |
| นามบัตร | Business Card | Printed name cards |
| โรลอัพ | Roll-up Banner | Portable retractable banner |
| ฟิวเจอร์บอร์ด | Futureboards | Foam board signage |

---

**End of PRD**

**Attached Documents:**
- `01-walkin-new-order.md` — Wireframe: Walk-in Order
- `02-design-approval-production.md` — Wireframe: Design → Approval → Production
- `03-pickup-final-payment.md` — Wireframe: Pickup & Payment
- `04-corporate-monthly-billing.md` — Wireframe: Corporate Billing
- `05-line-order-remote.md` — Wireframe: LINE Order
- `06-owner-daily-operations.md` — Wireframe: Owner Dashboard
- `user-journey-print-shop.md` — User Journey Map
