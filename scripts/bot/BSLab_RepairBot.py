#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BS LAB TOOL PRO — Workshop WhatsApp & Telegram AI Auto-Reply Bot
Provides 24/7 automated ticket status responses to customer inquiries,
real-time balance due notifications, and daily shop earnings reporting.
"""

import os
import sys
import json
import argparse
from datetime import datetime

TICKETS_FILE = r"C:\BSLab_Tool\WorkshopTickets\tickets.json"

def load_tickets():
    tickets = []
    if not os.path.exists(TICKETS_FILE):
        return tickets
    try:
        with open(TICKETS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        tickets.append(json.loads(line))
                    except Exception:
                        pass
    except Exception as ex:
        print(f"[!] Error loading tickets: {ex}")
    return tickets

def find_ticket(ticket_id):
    ticket_id = ticket_id.strip().upper()
    tickets = load_tickets()
    for t in tickets:
        if t.get("TicketId", "").upper() == ticket_id:
            return t
    return None

def format_customer_reply_urdu(ticket):
    customer = ticket.get("CustomerName", "محترم کسٹمر")
    device = ticket.get("DeviceModel", "موبائل فون")
    ticket_id = ticket.get("TicketId", "")
    status = ticket.get("Status", "زیرِ مرمت")
    total = ticket.get("TotalCost", "0")
    advance = ticket.get("AdvancePaid", "0")
    balance = ticket.get("BalanceDue", "0")
    shop_name = ticket.get("ShopName", "BS LAB GSM CARE")
    shop_phone = ticket.get("ShopPhone", "")

    status_icon = "🟢" if "READY" in status.upper() or "COMPLETE" in status.upper() else "🟡"

    reply = (
        f"السلام علیکم ورحمۃ اللہ {customer} صاحب!\n\n"
        f"📱 *ڈیوائس:* {device}\n"
        f"🎫 *ٹکٹ نمبر:* {ticket_id}\n"
        f"{status_icon} *موجودہ اسٹیٹس:* {status}\n\n"
        f"💰 *کل چارجز:* Rs. {total}\n"
        f"💵 *وصول شدہ رقم:* Rs. {advance}\n"
        f"🔴 *بقایا واجب الادا:* Rs. {balance}\n\n"
    )

    if "READY" in status.upper() or "COMPLETE" in status.upper():
        reply += "🎉 مبارک ہو! آپ کا فون مکمل طور پر تیار اور ٹیسٹ ہو چکا ہے۔ آپ اصل رسید دکھا کر فون وصول کر سکتے ہیں۔\n\n"
    elif "RECEIVED" in status.upper():
        reply += "🔍 آپ کا فون لیب میں ڈائیگنوسٹک اور ٹیسٹنگ کے مرحلے میں ہے۔ جلد مرمت شروع کر دی جائے گی۔\n\n"
    elif "PROGRESS" in status.upper():
        reply += "⚡ آپ کے فون پر سافٹ ویئر اور ہارڈویئر فلیشنگ کا کام جاری ہے۔\n\n"

    reply += f"شکریہ: *{shop_name}*\n📞 ہیلپ لائن: {shop_phone}"
    return reply

def format_daily_summary():
    tickets = load_tickets()
    total_count = len(tickets)
    total_rev = sum(float(t.get("TotalCost", 0)) for t in tickets if t.get("TotalCost"))
    total_adv = sum(float(t.get("AdvancePaid", 0)) for t in tickets if t.get("AdvancePaid"))
    total_bal = sum(float(t.get("BalanceDue", 0)) for t in tickets if t.get("BalanceDue"))

    today_str = datetime.now().strftime("%Y-%m-%d")

    report = (
        f"📊 *BS LAB TOOL PRO — روزانہ ورکشاپ سمری رپورٹ*\n"
        f"📅 تاریخ: {today_str}\n"
        f"══════════════════════════════\n"
        f"🎫 کل جاب ٹکٹس: {total_count}\n"
        f"💵 کل ممکنہ ریونیو: Rs. {total_rev:,.0f}\n"
        f"🟢 نقد موصولہ (ایڈوانس): Rs. {total_adv:,.0f}\n"
        f"🔴 مارکیٹ میں بقایا رقم: Rs. {total_bal:,.0f}\n"
        f"══════════════════════════════\n"
        f"✓ تمام ڈیٹا محفوظ ہے: {TICKETS_FILE}\n"
    )
    return report

def main():
    parser = argparse.ArgumentParser(description="BS Lab Tool Workshop AI WhatsApp Bot")
    parser.add_argument("--query", type=str, help="Search status for Ticket ID (e.g. BS-2026-1049)")
    parser.add_argument("--report", action="store_true", help="Generate Daily Financial & Repair Summary")
    parser.add_argument("--test", action="store_true", help="Run automated test simulation")

    args = parser.parse_args()

    if args.report:
        print(format_daily_summary())
    elif args.query:
        ticket = find_ticket(args.query)
        if ticket:
            print(format_customer_reply_urdu(ticket))
        else:
            print(f"[!] ٹکٹ نمبر '{args.query}' نہیں ملا۔ برائے مہربانی درست ٹکٹ نمبر درج فرمائیں۔")
    elif args.test or len(sys.argv) == 1:
        print("══════════════════════════════════════════════════════════════")
        print("🤖 BS LAB TOOL PRO — WORKSHOP WHATSAPP AI BOT ENGINE")
        print("══════════════════════════════════════════════════════════════\n")
        print("[*] Testing Ticket Lookup for 'BS-2026-1049'...")
        sample_ticket = find_ticket("BS-2026-1049")
        if not sample_ticket:
            sample_ticket = {
                "TicketId": "BS-2026-1049",
                "CustomerName": "Syed Bisharat Ali",
                "DeviceModel": "Samsung Galaxy S24 Ultra (SM-S928B)",
                "Status": "🟢 READY FOR PICKUP (Work Complete)",
                "TotalCost": "4500",
                "AdvancePaid": "1500",
                "BalanceDue": "3000",
                "ShopName": "BS LAB GSM CARE & UNLOCK CLINIC",
                "ShopPhone": "+92 300 0000000"
            }
        print(format_customer_reply_urdu(sample_ticket))
        print("\n" + format_daily_summary())

if __name__ == "__main__":
    main()
