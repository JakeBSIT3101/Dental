import customtkinter as ctk
import tkinter as tk
import datetime
import calendar
import random
import string
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    Image = None

from clinic_app.logic.treatment import get_basic_treatment
from clinic_app.db_mysql import (
    fetch_patients,
    fetch_appointments,
    fetch_dentists,
    fetch_treatments,
    insert_patient,
    insert_appointment,
    insert_payment,
    insert_patient_history,
    fetch_patient_history,
    fetch_payments,
)


class DashboardFrame(ctk.CTkFrame):
    """Main dashboard showing treatment helper after login."""

    def __init__(self, master: ctk.CTkBaseClass, username: str) -> None:
        super().__init__(master)
        self.username = username

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=0, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(7, weight=1)

        # Drawer toggle (top-left)
        top_bar = ctk.CTkFrame(body, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")
        self.drawer_open = False
        self.drawer_width = 0
        self.drawer_target_width = 240
        self.drawer = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color="#0f172a",
            border_color="#1f2937",
            border_width=1,
            width=0,
            height=500,
        )
        self.treatment_catalog: dict[str, dict] = {}
        self.selected_treatments: list[dict] = []
        self.payment_amount: float = 0.0
        self.patient_input_data: dict[str, str] = {}
        self.treatment_patient_name: str | None = None
        self.treatment_dentist_name: str | None = None
        self.treatment_patient_id: int | None = None
        self.treatment_dentist_id: int | None = None
        self.treatment_schedule: str | None = None

        toggle_btn = ctk.CTkButton(
            top_bar,
            text="Menu",
            width=120,
            fg_color="#1f2937",
            hover_color="#111827",
            command=self._toggle_drawer,
        )
        toggle_btn.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")

        # Drawer content
        for i, label in enumerate(["Patient history", "Treatments", "Appointments", "Patients", "Payment history"]):
            ctk.CTkButton(
                self.drawer,
                text=label,
                fg_color="#111827",
                hover_color="#0b1220",
                width=160,
                anchor="w",
                command=lambda name=label: self._show_module(name),
            ).grid(row=i, column=0, padx=12, pady=6, sticky="ew")

        # Main content area (switchable per module)
        self.content = ctk.CTkFrame(body, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(1, weight=1)

        self._render_dashboard()

    def _show_plan(self) -> None:
        self.status.configure(text="")
        try:
            age_value = self.age_entry.get().strip()
            if not age_value:
                raise ValueError("Enter an age.")
            age = int(age_value)
            reason = self.reason_combo.get()
            plan = get_basic_treatment(age, reason)

            self.result.configure(state="normal")
            self.result.delete("1.0", "end")
            self.result.insert(
                "1.0",
                (
                    f"Age: {plan['age']} ({plan['age_group']})\n"
                    f"Reason: {plan['reason']}\n\n"
                    f"Recommended Treatment:\n{plan['recommended_treatment']}\n\n"
                    f"Notes:\n{plan['notes']}"
                ),
            )
            self.result.configure(state="disabled")
        except ValueError as exc:
            self.status.configure(text=str(exc))
            self.result.configure(state="normal")
            self.result.delete("1.0", "end")
            self.result.configure(state="disabled")

    def _add_treatment_to_receipt(self, name: str) -> None:
        """Add treatment by name to current receipt selections."""
        if name not in self.treatment_catalog:
            self.status.configure(text=f"{name} not found in treatments table.")
            return
        row = self.treatment_catalog[name]
        fee = row.get("default_fee") or 0
        try:
            fee_val = float(fee)
        except (TypeError, ValueError):
            fee_val = 0.0
        self.selected_treatments.append({"name": name, "fee": fee_val})
        # Reset payment when items change
        self.payment_amount = 0.0
        self._update_receipt()

    def _handle_treatment_click(self, name: str) -> None:
        """Ensure patient is selected before adding treatment."""
        if not self.treatment_patient_name:
            self._prompt_treatment_patient()
            if not self.treatment_patient_name:
                return
        self._add_treatment_to_receipt(name)

    def _remove_latest_treatment(self) -> None:
        """Remove the most recently added treatment from the receipt."""
        if not self.selected_treatments:
            self.status.configure(text="No treatments to remove.")
            return
        self.selected_treatments.pop()
        self.payment_amount = 0.0  # reset payment when items change
        self._update_receipt()
        self.status.configure(text="Last treatment removed.")

    def _show_payment_modal(self) -> None:
        """Prompt for payment amount and update receipt."""
        total_due = getattr(self, "current_total", 0.0)
        top = ctk.CTkToplevel(self)
        top.title("Payment")
        top.geometry("320x200")
        top.grab_set()
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="Total due:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )
        ctk.CTkLabel(top, text=f"\u20B1{total_due:,.2f}").grid(
            row=0, column=1, padx=12, pady=(12, 4), sticky="e"
        )

        ctk.CTkLabel(top, text="Amount paid:").grid(
            row=1, column=0, padx=12, pady=8, sticky="w"
        )
        amount_entry = ctk.CTkEntry(top, placeholder_text="e.g., 1500")
        amount_entry.grid(row=1, column=1, padx=12, pady=8, sticky="ew")

        status_lbl = ctk.CTkLabel(top, text="", text_color="orange")
        status_lbl.grid(row=3, column=0, columnspan=2, padx=12, pady=(4, 0), sticky="w")

        def do_pay() -> None:
            try:
                amt = float(amount_entry.get().strip())
            except (TypeError, ValueError):
                status_lbl.configure(text="Enter a valid number.")
                return
            if amt < total_due:
                status_lbl.configure(text="Insufficient payment.")
                return
            if not self.treatment_patient_id or not self.treatment_dentist_id:
                status_lbl.configure(text="Select patient and dentist first.")
                return
            if not self.treatment_schedule:
                status_lbl.configure(text="Provide schedule before payment.")
                return

            reason = ", ".join(item["name"] for item in self.selected_treatments) or "Treatment"
            note_text = ""
            if hasattr(self, "treatment_note"):
                note_text = self.treatment_note.get("1.0", "end").strip()
                if note_text == getattr(self, "_note_placeholder", ""):
                    note_text = ""
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            ok_ins, msg_ins, appt_id = insert_appointment(
                self.treatment_patient_id,
                self.treatment_dentist_id,
                self.treatment_schedule,
                "scheduled",
                reason,
                note_text,
                created_at,
            )
            if not ok_ins or not appt_id:
                status_lbl.configure(text=msg_ins)
                return

            ref = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
            ok_pay, msg_pay = insert_payment(
                appointment_id=appt_id,
                patient_id=self.treatment_patient_id,
                amount=amt,
                method="cash",
                status="paid",
                reference_no=ref,
                remarks="Dr. Paolo De Leon",
            )
            if not ok_pay:
                status_lbl.configure(text=msg_pay)
                return
            # Successful payment: clear receipt.
            self.payment_amount = 0.0
            self.selected_treatments = []
            self.current_total = 0.0
            self._update_receipt()
            self.status.configure(text="Payment saved and receipt cleared.")
            top.destroy()

        ctk.CTkButton(top, text="Confirm", command=do_pay).grid(
            row=2, column=0, columnspan=2, padx=12, pady=12, sticky="ew"
        )

    
    def _update_receipt(self) -> None:
        """Render receipt text from selected treatments."""
        if not hasattr(self, "receipt_box"):
            return
        lines: list[str] = []
        lines.append("-" * 57)
        lines.append("TREATMENT DETAILS")
        lines.append("-" * 57)
        lines.append(f"{'No.':<4} {'Treatment':<22} {'Fee':>15}")
        lines.append("-" * 57)
        subtotal = 0.0
        for idx, item in enumerate(self.selected_treatments, start=1):
            subtotal += item["fee"]
            lines.append(f"{idx:<4} {item['name']:<22} ₱{item['fee']:>12,.2f}")
        lines.append("-" * 57)
        discount = 0.0
        total = subtotal - discount
        self.current_total = total
        lines.append(f"{'Subtotal:':<28} ₱{subtotal:>18,.2f}")
        lines.append(f"{'Discount:':<28} ₱{discount:>18,.2f}")
        lines.append("-" * 57)
        lines.append(f"{'TOTAL AMOUNT DUE:':<28} ₱{total:>18,.2f}")
        lines.append("-" * 57)
        if self.payment_amount:
            change = self.payment_amount - total
            lines.append(f"{'Payment:':<28} ₱{self.payment_amount:>18,.2f}")
            lines.append(f"{'Change:':<28} ₱{change:>18,.2f}")
            lines.append("-" * 57)

        self.receipt_box.configure(state="normal")
        self.receipt_box.delete("1.0", "end")
        self.receipt_box.insert("1.0", "\n".join(lines))
        self.receipt_box.configure(state="disabled")

    def _focus_note(self) -> None:
        if hasattr(self, "treatment_note"):
            self.treatment_note.focus_set()

    def _clear_note_placeholder(self, event=None) -> None:
        if hasattr(self, "treatment_note"):
            text = self.treatment_note.get("1.0", "end").strip()
            if text == self._note_placeholder:
                self.treatment_note.delete("1.0", "end")

    def _restore_note_placeholder(self, event=None) -> None:
        if hasattr(self, "treatment_note"):
            text = self.treatment_note.get("1.0", "end").strip()
            if not text:
                self.treatment_note.insert("1.0", self._note_placeholder)

    def _prompt_patient_field(self, field: str) -> None:
        """Ask for a patient field value and store it temporarily."""
        dialog = ctk.CTkInputDialog(
            text=f"Enter {field.replace('_', ' ')}:",
            title="Patient info",
        )
        value = dialog.get_input()
        if value is None:
            return
        self.patient_input_data[field] = value
        # Show current collected fields in status
        summary = ", ".join(f"{k}: {v}" for k, v in self.patient_input_data.items())
        self.status.configure(text=f"Collected: {summary}")

    def _prompt_treatment_patient(self) -> None:
        """Prompt for patient selection before adding treatments."""
        ok, msg, rows = fetch_patients()
        if not ok or not rows:
            self.status.configure(text=msg or "No patients available.")
            return
        names = []
        patient_map: dict[str, int] = {}
        for r in rows:
            full_name = f"{r.get('first_name','').strip()} {r.get('last_name','').strip()}".strip()
            if full_name:
                names.append(full_name)
                if r.get("patient_id") is not None:
                    patient_map[full_name] = r.get("patient_id")
        ok_den, msg_den, dentists = fetch_dentists()
        dentist_names = []
        dentist_map: dict[str, int] = {}
        if ok_den and dentists:
            for r in dentists:
                name = (
                    r.get("full_name")
                    or r.get("fullname")
                    or f"{r.get('first_name','').strip()} {r.get('last_name','').strip()}".strip()
                ).strip()
                if name:
                    dentist_names.append(name)
                    if r.get("dentist_id") is not None:
                        dentist_map[name] = r.get("dentist_id")
        if not names:
            self.status.configure(text="No patients available.")
            return
        if not dentist_names:
            self.status.configure(text=msg_den or "No dentists available.")
            return

        modal = ctk.CTkToplevel(self)
        modal.title("Select patient and dentist")
        modal.geometry("420x320")
        modal.grab_set()
        modal.grid_columnconfigure(0, weight=1)
        modal.grid_columnconfigure(1, weight=1)

        # Row: patient label + add button
        patient_bar = ctk.CTkFrame(modal, fg_color="transparent")
        patient_bar.grid(row=0, column=0, columnspan=3, padx=12, pady=(12, 4), sticky="ew")
        patient_bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(patient_bar, text="Choose patient for treatments:").grid(row=0, column=0, sticky="w")
        def _refresh_lists():
            ok_new, _, new_rows = fetch_patients()
            if ok_new and new_rows:
                new_names = []
                patient_map.clear()
                for r in new_rows:
                    nm = f"{r.get('first_name','').strip()} {r.get('last_name','').strip()}".strip()
                    if nm:
                        new_names.append(nm)
                        if r.get("patient_id") is not None:
                            patient_map[nm] = r.get("patient_id")
                if new_names:
                    combo_patient.configure(values=new_names)
                    combo_patient.set(new_names[0])
            return
        ctk.CTkButton(
            patient_bar,
            text="+",
            width=32,
            height=32,
            fg_color="#0ea5e9",
            hover_color="#0284c7",
            text_color="#ffffff",
            command=lambda: (self._show_add_patient_modal(), self.after(500, _refresh_lists)),
        ).grid(row=0, column=1, padx=(8, 0), sticky="e")

        combo_patient = ctk.CTkComboBox(modal, values=names, state="readonly")
        combo_patient.set(names[0])
        combo_patient.grid(row=1, column=0, columnspan=3, padx=12, pady=4, sticky="ew")

        ctk.CTkLabel(modal, text="Choose dentist:").grid(
            row=2, column=0, columnspan=2, padx=12, pady=(12, 4), sticky="w"
        )
        combo_dentist = ctk.CTkComboBox(modal, values=dentist_names, state="readonly")
        combo_dentist.set(dentist_names[0])
        combo_dentist.grid(row=3, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        sched_frame = ctk.CTkFrame(modal, fg_color="transparent")
        sched_frame.grid(row=4, column=0, columnspan=2, padx=12, pady=(12, 4), sticky="ew")
        sched_frame.grid_columnconfigure(1, weight=1)
        sched_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(sched_frame, text="Select schedule:").grid(
            row=0, column=0, padx=(0, 8), pady=(0, 4), sticky="w"
        )
        sched_date = ctk.CTkEntry(sched_frame, placeholder_text="YYYY-MM-DD")
        sched_date.grid(row=0, column=1, padx=(0, 4), pady=(0, 4), sticky="ew")
        ctk.CTkButton(
            sched_frame,
            text="📅",
            width=40,
            command=lambda ent=sched_date: self._show_calendar_modal(ent),
        ).grid(row=0, column=2, padx=(0, 8), pady=(0, 4), sticky="w")
        sched_time = ctk.CTkEntry(sched_frame, placeholder_text="HH:MM AM/PM")
        sched_time.grid(row=0, column=3, padx=(0, 4), pady=(0, 4), sticky="ew")
        ctk.CTkButton(
            sched_frame,
            text="⏰",
            width=40,
            command=lambda ent=sched_time: self._show_time_modal(ent),
        ).grid(row=0, column=4, padx=(0, 0), pady=(0, 4), sticky="w")

        status_lbl = ctk.CTkLabel(modal, text="", text_color="orange")
        status_lbl.grid(row=6, column=0, columnspan=2, padx=12, pady=(4, 0), sticky="w")

        def confirm_patient() -> None:
            pval = combo_patient.get().strip()
            dval = combo_dentist.get().strip()
            sdate = sched_date.get().strip()
            stime = sched_time.get().strip()
            if not pval:
                status_lbl.configure(text="Select a patient.")
                return
            if not dval:
                status_lbl.configure(text="Select a dentist.")
                return
            if not sdate or not stime:
                status_lbl.configure(text="Enter schedule date/time.")
                return
            self.treatment_patient_name = pval
            self.treatment_dentist_name = dval
            self.treatment_patient_id = patient_map.get(pval)
            self.treatment_dentist_id = dentist_map.get(dval)
            self.treatment_schedule = f"{sdate} {stime}"
            self.status.configure(
                text=f"Patient: {pval} | Dentist: {dval} | Schedule: {self.treatment_schedule}"
            )
            modal.destroy()

        ctk.CTkButton(
            modal,
            text="Confirm",
            fg_color="#123055",
            hover_color="#0c2340",
            text_color="#ffffff",
            command=confirm_patient,
        ).grid(row=7, column=0, columnspan=2, padx=12, pady=12, sticky="ew")

    def _show_calendar_modal(self, target_entry: ctk.CTkEntry) -> None:
        """Simple calendar picker to fill YYYY-MM-DD."""
        today = datetime.date.today()
        year = today.year
        month = today.month

        top = ctk.CTkToplevel(self)
        top.title("Pick a date")
        top.geometry("340x320")
        top.grab_set()
        top.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        header = ctk.CTkLabel(top, text="")
        header.grid(row=0, column=0, columnspan=7, pady=(8, 4))

        def render(y: int, m: int) -> None:
            header.configure(text=f"{calendar.month_name[m]} {y}")
            # clear old day buttons
            for widget in top.grid_slaves():
                info = widget.grid_info()
                if int(info.get('row', 1)) >= 2:
                    widget.destroy()
            month_cal = calendar.monthcalendar(y, m)
            weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
            for idx, wd in enumerate(weekdays):
                ctk.CTkLabel(top, text=wd, text_color="#9ca3af").grid(row=1, column=idx, pady=2)
            for r, week in enumerate(month_cal, start=2):
                for c, day in enumerate(week):
                    if day == 0:
                        continue
                    btn = ctk.CTkButton(
                        top,
                        text=str(day),
                        width=32,
                        fg_color="#1f2937",
                        hover_color="#0b1220",
                        command=lambda d=day, yy=y, mm=m: pick(yy, mm, d),
                    )
                    btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")

        def pick(y: int, m: int, d: int) -> None:
            target_entry.delete(0, "end")
            target_entry.insert(0, f"{y:04d}-{m:02d}-{d:02d}")
            top.destroy()

        def shift(delta: int) -> None:
            nonlocal year, month
            month += delta
            if month < 1:
                month, year = 12, year - 1
            elif month > 12:
                month, year = 1, year + 1
            render(year, month)

        ctk.CTkButton(top, text="<", width=32, command=lambda: shift(-1)).grid(row=0, column=0, pady=(8, 4))
        ctk.CTkButton(top, text=">", width=32, command=lambda: shift(1)).grid(row=0, column=6, pady=(8, 4))

        render(year, month)

    def _show_time_modal(self, target_entry: ctk.CTkEntry) -> None:
        """Time picker with hour/minute and AM/PM."""
        top = ctk.CTkToplevel(self)
        top.title("Pick time")
        top.geometry("260x180")
        top.grab_set()
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(2, weight=1)

        hours = [f"{h:02d}" for h in range(1, 13)]
        minutes = [f"{m:02d}" for m in range(0, 60, 5)]
        meridiem = ["AM", "PM"]

        ctk.CTkLabel(top, text="Hour").grid(row=0, column=0, padx=8, pady=(10, 2), sticky="w")
        ctk.CTkLabel(top, text="Min").grid(row=0, column=1, padx=8, pady=(10, 2), sticky="w")
        ctk.CTkLabel(top, text="AM/PM").grid(row=0, column=2, padx=8, pady=(10, 2), sticky="w")

        combo_h = ctk.CTkComboBox(top, values=hours, state="readonly")
        combo_h.set(hours[0])
        combo_h.grid(row=1, column=0, padx=8, pady=4, sticky="ew")

        combo_m = ctk.CTkComboBox(top, values=minutes, state="readonly")
        combo_m.set(minutes[0])
        combo_m.grid(row=1, column=1, padx=8, pady=4, sticky="ew")

        combo_ap = ctk.CTkComboBox(top, values=meridiem, state="readonly")
        combo_ap.set(meridiem[0])
        combo_ap.grid(row=1, column=2, padx=8, pady=4, sticky="ew")

        def confirm() -> None:
            time_str = f"{combo_h.get()}:{combo_m.get()} {combo_ap.get()}"
            target_entry.delete(0, "end")
            target_entry.insert(0, time_str)
            top.destroy()

        ctk.CTkButton(top, text="Confirm", command=confirm).grid(
            row=2, column=0, columnspan=3, padx=12, pady=12, sticky="ew"
        )

    def _show_add_patient_modal(self) -> None:
        """Modal to capture new patient info."""
        top = ctk.CTkToplevel(self)
        top.title("Add patient")
        top.geometry("420x360")
        top.grab_set()
        for i in range(2):
            top.grid_columnconfigure(i, weight=1)

        fields = [
            ("first_name", "First name"),
            ("last_name", "Last name"),
            ("birth_date", "Birth date (YYYY-MM-DD)"),
            ("age_group", "Age group"),
            ("gender", "Gender"),
            ("phone", "Phone"),
            ("email", "Email"),
            ("address", "Address"),
        ]
        entries = {}

        for idx, (key, label) in enumerate(fields):
            ctk.CTkLabel(top, text=label).grid(row=idx, column=0, padx=8, pady=6, sticky="w")
            if key == "age_group":
                combo = ctk.CTkComboBox(
                    top,
                    values=["child", "adult", "old"],
                    state="readonly",
                )
                combo.set("child")
                combo.grid(row=idx, column=1, padx=8, pady=6, sticky="ew")
                entries[key] = combo
            else:
                ent = ctk.CTkEntry(top)
                ent.grid(row=idx, column=1, padx=8, pady=6, sticky="ew")
                entries[key] = ent

        status_lbl = ctk.CTkLabel(top, text="", text_color="orange")
        status_lbl.grid(row=len(fields), column=0, columnspan=2, padx=8, pady=(4, 0), sticky="w")

        def confirm() -> None:
            data = {}
            for key, widget in entries.items():
                if isinstance(widget, ctk.CTkComboBox):
                    data[key] = widget.get().strip()
                else:
                    data[key] = widget.get().strip()

            ok, msg = insert_patient(
                data.get("first_name", ""),
                data.get("last_name", ""),
                data.get("birth_date", ""),
                data.get("age_group", ""),
                data.get("gender", ""),
                data.get("phone", ""),
                data.get("email", ""),
                data.get("address", ""),
            )
            if not ok:
                status_lbl.configure(text=msg)
                return
            try:
                if hasattr(self, "status") and self.status.winfo_exists():
                    self.status.configure(text=msg)
                if hasattr(self, "status_patients") and self.status_patients.winfo_exists():
                    self.status_patients.configure(text=msg)
            except Exception:
                pass
            # Show success modal
            ok_modal = ctk.CTkToplevel(self)
            ok_modal.title("Success")
            ok_modal.geometry("260x120")
            ok_modal.grab_set()
            ok_modal.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(ok_modal, text="Add Patient Successful").grid(
                row=0, column=0, padx=12, pady=(16, 8), sticky="n"
            )
            ctk.CTkButton(
                ok_modal,
                text="OK",
                fg_color="#123055",
                hover_color="#0c2340",
                text_color="#ffffff",
                command=ok_modal.destroy,
            ).grid(row=1, column=0, padx=12, pady=(4, 12), sticky="ew")

            top.destroy()
            # Refresh patients view
            self._render_patients()

        ctk.CTkButton(
            top,
            text="Confirm",
            fg_color="#123055",
            hover_color="#0c2340",
            text_color="#ffffff",
            command=confirm,
        ).grid(row=len(fields), column=0, columnspan=2, padx=8, pady=(4, 4), sticky="ew")

    def _toggle_drawer(self) -> None:
        """Show/hide the left drawer of modules."""
        if self.drawer_open:
            self._animate_drawer(opening=False)
        else:
            # Place at left and animate open; stretch height to current frame height.
            self.update_idletasks()
            h = max(self.winfo_height(), 500)
            self.drawer.configure(height=h)
            self.drawer.place(x=8, y=8)
            self.drawer.lift()
            self.drawer_width = 0
            self._animate_drawer(opening=True)
        self.drawer_open = not self.drawer_open

    def _show_module(self, name: str) -> None:
        """Open selected module and close any previous module window."""
        if self.drawer_open:
            self._toggle_drawer()

        if name.lower().startswith("patient history"):
            self._render_patient_history()
        elif name.lower().startswith("patients"):
            self._render_patients()
        elif name.lower().startswith("treat"):
            self._render_treatments()
        elif name.lower().startswith("appoint"):
            self._render_appointments()
        elif name.lower().startswith("payment"):
            self._render_payment_history()
        else:
            self._render_dashboard()

    def _animate_drawer(self, opening: bool, step: int = 16, delay_ms: int = 10) -> None:
        """Simple slide animation for the drawer."""
        target = self.drawer_target_width if opening else 0
        if opening:
            self.drawer_width = min(self.drawer_width + step, target)
        else:
            self.drawer_width = max(self.drawer_width - step, target)

        if self.drawer_width <= 0 and not opening:
            self.drawer.place_forget()
            return

        self.drawer.configure(width=self.drawer_width)
        if self.drawer_width != target:
            self.after(delay_ms, lambda: self._animate_drawer(opening, step, delay_ms))

    def _clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def _render_dashboard(self) -> None:
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            self.content,
            text=f"Welcome, {self.username}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(0, 4), sticky="w")

        ctk.CTkLabel(
            self.content,
            text="Enter patient age and visit reason to draft a simple plan.",
        ).grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")

        logo_frame = ctk.CTkFrame(self.content, fg_color="#0b1220", corner_radius=12)
        logo_frame.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        logo_frame.grid_columnconfigure(0, weight=1)
        logo_frame.grid_rowconfigure(0, weight=1)
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        if Image and logo_path.exists():
            img = Image.open(logo_path)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(320, 320))
            ctk.CTkLabel(logo_frame, image=ctk_img, text="").grid(row=0, column=0, padx=12, pady=12)
        else:
            ctk.CTkLabel(
                logo_frame,
                text="Dental Clinic",
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color="#e5e7eb",
            ).grid(row=0, column=0, padx=12, pady=24)

        form = ctk.CTkFrame(self.content)
        form.grid(row=4, column=0, padx=12, pady=8, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Age:").grid(row=0, column=0, padx=(10, 8), pady=8, sticky="e")
        self.age_entry = ctk.CTkEntry(form, placeholder_text="e.g., 30")
        self.age_entry.grid(row=0, column=1, padx=(0, 10), pady=8, sticky="ew")

        ctk.CTkLabel(form, text="Reason:").grid(row=1, column=0, padx=(10, 8), pady=8, sticky="e")
        self.reason_combo = ctk.CTkComboBox(
            form,
            values=["checkup", "cleaning", "toothache", "braces", "other"],
            state="readonly",
        )
        self.reason_combo.set("checkup")
        self.reason_combo.grid(row=1, column=1, padx=(0, 10), pady=8, sticky="ew")

        ctk.CTkButton(
            self.content,
            text="Generate Plan",
            command=self._show_plan,
        ).grid(row=5, column=0, padx=12, pady=(0, 8), sticky="e")

        self.result = ctk.CTkTextbox(self.content, wrap="word")
        self.result.grid(row=6, column=0, padx=12, pady=8, sticky="nsew")
        self.result.configure(state="disabled")

        self.status = ctk.CTkLabel(self.content, text="", text_color="orange")
        self.status.grid(row=7, column=0, padx=12, pady=(4, 0), sticky="w")

    def _render_treatments(self) -> None:
        """Show treatment shortcut buttons."""
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.content,
            text="Treatments",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(0, 8), sticky="w")

        # Load catalog once
        if not self.treatment_catalog:
            ok, msg, rows = fetch_treatments()
            if not ok:
                ctk.CTkLabel(self.content, text=msg, text_color="orange").grid(
                    row=1, column=0, padx=12, pady=12, sticky="w"
                )
                return
            for r in rows:
                name = r.get("name")
                if not name:
                    continue
                self.treatment_catalog[name] = r
        # Require patient selection
        self._prompt_treatment_patient()

        # Layout: buttons cluster on the left, receipt column on the right
        tray = ctk.CTkFrame(self.content, fg_color="transparent")
        tray.grid(row=1, column=0, padx=(8, 12), pady=(4, 12), sticky="nw")
        tray.grid_columnconfigure((0, 1), weight=1)
        right_col = ctk.CTkFrame(self.content, fg_color="transparent")
        right_col.grid(row=1, column=1, padx=(12, 16), pady=(4, 12), sticky="nw")
        right_col.grid_columnconfigure(0, weight=1)

        buttons = ["Cleaning", "Fluoride", "Filling", "Extraction", "Dentures"]
        # Left column: 3 buttons; Right column: 2 buttons stacked at top.
        positions = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)]
        for (r, c), label in zip(positions, buttons):
            ctk.CTkButton(
                tray,
                text=label,
                fg_color="#ffffff",
                hover_color="#e5e7eb",
                height=110,
                corner_radius=18,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#0f172a",
                command=lambda name=label: self._handle_treatment_click(name),
            ).grid(row=r, column=c, padx=12, pady=12, sticky="nsew")

        # Add note pill
        ctk.CTkButton(
            tray,
            text="add note",
            fg_color="#2f3440",
            hover_color="#1f2937",
            text_color="#dcd7b1",
            corner_radius=18,
            width=90,
            height=32,
            command=self._focus_note,
        ).grid(row=3, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="w")

        note_frame = ctk.CTkFrame(tray, fg_color="#ffffff", corner_radius=18)
        note_frame.grid(row=4, column=0, columnspan=2, padx=12, pady=12, sticky="nsew")
        note_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(note_frame, text="Note", text_color="#0f172a").grid(
            row=0, column=0, padx=8, pady=(8, 4), sticky="w"
        )
        self.treatment_note = ctk.CTkTextbox(note_frame, fg_color="#f5f5f5", text_color="#0f172a", height=80)
        self.treatment_note.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        # placeholder behavior
        self._note_placeholder = "type note..."
        self.treatment_note.insert("1.0", self._note_placeholder)
        self.treatment_note.bind("<FocusIn>", self._clear_note_placeholder)
        self.treatment_note.bind("<FocusOut>", self._restore_note_placeholder)

        # Action bar above receipt
        bar = ctk.CTkFrame(right_col, fg_color="transparent")
        bar.grid(row=0, column=0, padx=0, pady=(0, 4), sticky="w")
        ctk.CTkButton(
            bar,
            text="Remove",
            fg_color="#dc2626",
            hover_color="#b91c1c",
            text_color="#ffffff",
            corner_radius=14,
            width=120,
            height=36,
            command=self._remove_latest_treatment,
        ).grid(row=0, column=0, padx=(0, 8), pady=0)
        ctk.CTkButton(
            bar,
            text="Pay",
            fg_color="#123055",
            hover_color="#0c2340",
            text_color="#ffffff",
            corner_radius=14,
            width=120,
            height=36,
            command=self._show_payment_modal,
        ).grid(row=0, column=1, padx=(0, 0), pady=0)

        receipt = ctk.CTkFrame(
            right_col,
            fg_color="#ffffff",
            corner_radius=18,
        )
        receipt.grid(row=1, column=0, padx=0, pady=(0, 0), sticky="nsew")
        receipt.grid_columnconfigure(0, weight=1)
        receipt.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(receipt, text="RECEIPT", text_color="#0f172a").grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )
        self.receipt_box = ctk.CTkTextbox(
            receipt,
            fg_color="#ffffff",
            text_color="#0f172a",
            font=("Consolas", 12),
            wrap="none",
        )
        self.receipt_box.grid(row=1, column=0, padx=12, pady=(4, 12), sticky="nsew")
        self.receipt_box.configure(state="disabled")
        self._update_receipt()

        self.status = ctk.CTkLabel(self.content, text="", text_color="orange")
        self.status.grid(row=7, column=0, padx=12, pady=(4, 0), sticky="w")

    def _render_patient_history(self) -> None:
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.content,
            text="Patient history",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(0, 8), sticky="w")

        ok_hist, msg_hist, hist_rows = fetch_patient_history()
        if not ok_hist:
            ctk.CTkLabel(self.content, text=msg_hist, text_color="orange").grid(
                row=1, column=0, padx=12, pady=12, sticky="w"
            )
            return

        ok_pat, _, patient_rows = fetch_patients()
        ok_app, _, appt_rows = fetch_appointments()
        patient_map = {}
        if ok_pat and patient_rows:
            for r in patient_rows:
                pid = r.get("patient_id")
                name = f"{r.get('first_name','').strip()} {r.get('last_name','').strip()}".strip()
                patient_map[pid] = name or str(pid)
        appt_map = {}
        if ok_app and appt_rows:
            for r in appt_rows:
                appt_map[r.get("appointment_id")] = r

        search_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type to filter history")
        search_entry.grid(row=0, column=1, padx=(0, 8), pady=4, sticky="ew")

        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        scroll.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_rowconfigure(0, weight=1)
        scroll.grid_rowconfigure(0, weight=1)

        columns = [
            ("patient", "Patient", 2),
            ("visit_date", "Visit date", 1),
            ("diagnosis", "Diagnosis", 2),
            ("treatment_given", "Treatment", 2),
            ("prescription", "Prescription", 2),
            ("follow_up_date", "Follow-up", 1),
            ("notes", "Notes", 3),
            ("appointment", "Appointment", 2),
        ]
        minsize = {
            "patient": 180,
            "visit_date": 160,
            "diagnosis": 180,
            "treatment_given": 200,
            "prescription": 200,
            "follow_up_date": 160,
            "notes": 260,
            "appointment": 200,
        }

        table = ctk.CTkFrame(
            scroll,
            corner_radius=6,
            fg_color="#ffffff",
            border_width=1,
            border_color="#e5e7eb",
        )
        table.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        table.grid_columnconfigure(tuple(range(len(columns))), weight=1)

        header_font = ctk.CTkFont(size=12, weight="bold")
        cell_font = ctk.CTkFont(size=12)

        for c_idx, (key, header, weight) in enumerate(columns):
            table.grid_columnconfigure(c_idx, weight=weight, minsize=minsize.get(key, 120))
            ctk.CTkLabel(
                table,
                text=header,
                font=header_font,
                text_color="#111827",
                fg_color="#f5f5f5",
            ).grid(row=0, column=c_idx, padx=4, pady=4, sticky="nsew")

        self.history_rows = hist_rows or []

        def build_table(row_data: list[dict]) -> None:
            for child in table.grid_slaves():
                if int(child.grid_info().get("row", 1)) > 0:
                    child.destroy()

            if not row_data:
                ctk.CTkLabel(table, text="No history records match.").grid(
                    row=1, column=0, padx=8, pady=8, sticky="w", columnspan=len(columns)
                )
                return

            for r_idx, row in enumerate(row_data, start=1):
                bg = "#ffffff" if r_idx % 2 else "#f9fafb"
                pid = row.get("patient_id")
                patient_name = patient_map.get(pid, pid)
                appt = appt_map.get(row.get("appointment_id"))
                appt_label = ""
                if appt:
                    appt_label = f"{appt.get('scheduled_at','')}"
                values = {
                    "patient": patient_name,
                    "visit_date": row.get("visit_date", ""),
                    "diagnosis": row.get("diagnosis", ""),
                    "treatment_given": row.get("treatment_given", ""),
                    "prescription": row.get("prescription", ""),
                    "follow_up_date": row.get("follow_up_date", ""),
                    "notes": row.get("notes", ""),
                    "appointment": appt_label,
                }
                for c_idx, (key, _, _) in enumerate(columns):
                    ctk.CTkLabel(
                        table,
                        text=str(values.get(key, "")),
                        font=cell_font,
                        text_color="#111827",
                        anchor="w",
                        fg_color=bg,
                    ).grid(row=r_idx, column=c_idx, padx=4, pady=4, sticky="nsew")

        build_table(self.history_rows)

        def apply_filter(*_args) -> None:
            term = search_entry.get().strip().lower()
            if not term:
                filtered = self.history_rows
            else:
                filtered = []
                for r in self.history_rows:
                    haystack = " ".join(str(v) for v in r.values()).lower()
                    if term in haystack:
                        filtered.append(r)
            build_table(filtered)

        search_entry.bind("<KeyRelease>", apply_filter)

    def _render_payment_history(self) -> None:
        """Display payments table."""
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.content,
            text="Payment history",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(0, 8), sticky="w")

        ok_pay, msg_pay, pay_rows = fetch_payments()
        if not ok_pay:
            ctk.CTkLabel(self.content, text=msg_pay, text_color="orange").grid(
                row=1, column=0, padx=12, pady=12, sticky="w"
            )
            return

        ok_pat, _, patient_rows = fetch_patients()
        ok_app, _, appt_rows = fetch_appointments()
        patient_map = {}
        if ok_pat and patient_rows:
            for r in patient_rows:
                pid = r.get("patient_id")
                name = f"{r.get('first_name','').strip()} {r.get('last_name','').strip()}".strip()
                patient_map[pid] = name or str(pid)
        appt_map = {}
        if ok_app and appt_rows:
            for r in appt_rows:
                appt_map[r.get("appointment_id")] = r

        search_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type to filter payments")
        search_entry.grid(row=0, column=1, padx=(0, 8), pady=4, sticky="ew")

        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        scroll.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        columns = [
            ("patient", "Patient", 2),
            ("appointment", "Appointment", 2),
            ("amount", "Amount", 1),
            ("payment_date", "Payment date", 2),
            ("method", "Method", 1),
            ("status", "Status", 1),
            ("reference_no", "Reference", 2),
            ("remarks", "Remarks", 2),
        ]

        table = ctk.CTkFrame(
            scroll,
            corner_radius=6,
            fg_color="#ffffff",
            border_width=1,
            border_color="#e5e7eb",
        )
        table.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        table.grid_columnconfigure(tuple(range(len(columns))), weight=1)

        header_font = ctk.CTkFont(size=12, weight="bold")
        cell_font = ctk.CTkFont(size=12)

        for c_idx, (_, header, weight) in enumerate(columns):
            table.grid_columnconfigure(c_idx, weight=weight)
            ctk.CTkLabel(
                table,
                text=header,
                font=header_font,
                text_color="#111827",
                fg_color="#f5f5f5",
            ).grid(row=0, column=c_idx, padx=4, pady=4, sticky="nsew")

        self.pay_rows = pay_rows or []

        def build_table(row_data: list[dict]) -> None:
            for child in table.grid_slaves():
                if int(child.grid_info().get("row", 1)) > 0:
                    child.destroy()

            if not row_data:
                ctk.CTkLabel(table, text="No payment records match.").grid(
                    row=1, column=0, padx=8, pady=8, sticky="w", columnspan=len(columns)
                )
                return

            for r_idx, row in enumerate(row_data, start=1):
                bg = "#ffffff" if r_idx % 2 else "#f9fafb"
                pid = row.get("patient_id")
                patient_name = patient_map.get(pid, pid)
                appt = appt_map.get(row.get("appointment_id"))
                appt_label = ""
                if appt:
                    appt_label = appt.get("scheduled_at", "")
                values = {
                    "patient": patient_name,
                    "appointment": appt_label,
                    "amount": row.get("amount", ""),
                    "payment_date": row.get("payment_date", ""),
                    "method": row.get("method", ""),
                    "status": row.get("status", ""),
                    "reference_no": row.get("reference_no", ""),
                    "remarks": row.get("remarks", ""),
                }
                for c_idx, (key, _, _) in enumerate(columns):
                    ctk.CTkLabel(
                        table,
                        text=str(values.get(key, "")),
                        font=cell_font,
                        text_color="#111827",
                        anchor="w",
                        fg_color=bg,
                    ).grid(row=r_idx, column=c_idx, padx=4, pady=4, sticky="nsew")

        build_table(self.pay_rows)

        def apply_filter(*_args) -> None:
            term = search_entry.get().strip().lower()
            if not term:
                filtered = self.pay_rows
            else:
                filtered = []
                for r in self.pay_rows:
                    haystack = " ".join(str(v) for v in r.values()).lower()
                    if term in haystack:
                        filtered.append(r)
            build_table(filtered)

        search_entry.bind("<KeyRelease>", apply_filter)

    def _render_patients(self) -> None:
        """Patients module with input prompt buttons and table."""
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self.content,
            text="Patients",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(0, 8), sticky="w")

        ok, msg, rows = fetch_patients()
        if not ok:
            ctk.CTkLabel(self.content, text=msg, text_color="orange").grid(
                row=1, column=0, padx=12, pady=12, sticky="w"
            )
            return

        # Cache rows for filtering
        self.patient_rows = rows or []

        search_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type to filter patients")
        search_entry.grid(row=0, column=1, padx=(0, 8), pady=4, sticky="ew")

        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        scroll.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self.patient_table_holder = ctk.CTkFrame(scroll, fg_color="transparent")
        self.patient_table_holder.grid(row=0, column=0, sticky="nsew")

        columns = [
            ("name", "Name", 3),
            ("birth_date", "Birth date", 2),
            ("age_group", "Age group", 1),
            ("gender", "Gender", 1),
            ("phone", "Phone", 2),
            ("address", "Address", 4),
            ("created_at", "Created", 2),
        ]
        minsize = {
            "name": 160,
            "birth_date": 140,
            "age_group": 100,
            "gender": 100,
            "phone": 150,
            "address": 240,
            "created_at": 160,
        }

        def build_table(row_data: list[dict]) -> None:
            for child in self.patient_table_holder.winfo_children():
                child.destroy()

            if not row_data:
                ctk.CTkLabel(self.patient_table_holder, text="No patient records found.").grid(
                    row=0, column=0, padx=8, pady=8, sticky="w"
                )
                return

            table = ctk.CTkFrame(
                self.patient_table_holder,
                corner_radius=6,
                fg_color="#ffffff",
                border_width=1,
                border_color="#e5e7eb",
            )
            table.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
            table.grid_columnconfigure(tuple(range(len(columns))), weight=1)

            header_font = ctk.CTkFont(size=12, weight="bold")
            cell_font = ctk.CTkFont(size=12)

            for c_idx, (key, header, weight) in enumerate(columns):
                table.grid_columnconfigure(c_idx, weight=weight, minsize=minsize.get(key, 120))
                ctk.CTkLabel(
                    table,
                    text=header,
                    font=header_font,
                    text_color="#111827",
                    fg_color="#f5f5f5",
                ).grid(row=0, column=c_idx, padx=4, pady=4, sticky="nsew")

            for r_idx, row in enumerate(row_data, start=1):
                bg = "#ffffff" if r_idx % 2 else "#f9fafb"
                full_name = f"{row.get('first_name','').strip()} {row.get('last_name','').strip()}".strip()
                values = {
                    "name": full_name or row.get("first_name", "") or row.get("last_name", ""),
                    "birth_date": row.get("birth_date", ""),
                    "age_group": row.get("age_group", ""),
                    "gender": row.get("gender", ""),
                    "phone": row.get("phone", ""),
                    "address": row.get("address", ""),
                    "created_at": row.get("created_at", ""),
                }
                for c_idx, (key, _, _) in enumerate(columns):
                    ctk.CTkLabel(
                        table,
                        text=str(values.get(key, "")),
                        font=cell_font,
                        text_color="#111827",
                        anchor="w",
                        fg_color=bg,
                    ).grid(row=r_idx, column=c_idx, padx=4, pady=4, sticky="nsew")

        build_table(self.patient_rows)

        def apply_filter(*_args) -> None:
            term = search_entry.get().strip().lower()
            if not term:
                filtered = self.patient_rows
            else:
                filtered = []
                for r in self.patient_rows:
                    for val in r.values():
                        if term in str(val).lower():
                            filtered.append(r)
                            break
            build_table(filtered)

        search_entry.bind("<KeyRelease>", apply_filter)

        # Add button under the table, bottom right
        add_wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        add_wrap.grid(row=4, column=0, padx=12, pady=(0, 12), sticky="e")
        ctk.CTkButton(
            add_wrap,
            text="Add",
            fg_color="#ffffff",
            hover_color="#e5e7eb",
            text_color="#0f172a",
            width=100,
            command=self._show_add_patient_modal,
        ).grid(row=0, column=0, padx=0, pady=0, sticky="e")

        self.status_patients = ctk.CTkLabel(self.content, text="", text_color="orange")
        self.status_patients.grid(row=5, column=0, padx=12, pady=(4, 0), sticky="w")

    def _render_appointments(self) -> None:
        """Display appointments table."""
        self._clear_content()
        # Reset grid weights so leftover layouts (e.g., Treatments two-column) don't compress the table
        for col in range(3):
            self.content.grid_columnconfigure(col, weight=0)
        self.content.grid_columnconfigure(0, weight=1)
        for row in range(3):
            self.content.grid_rowconfigure(row, weight=0)
        self.content.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.content,
            text="Appointments",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(0, 8), sticky="w")

        ok, msg, rows = fetch_appointments()
        if not ok:
            ctk.CTkLabel(self.content, text=msg, text_color="orange").grid(
                row=1, column=0, padx=12, pady=12, sticky="w"
            )
            return

        ok_pat, _, patient_rows = fetch_patients()
        ok_den, _, dentist_rows = fetch_dentists()
        patient_map = {}
        if ok_pat and patient_rows:
            for r in patient_rows:
                pid = r.get("patient_id")
                name = f"{r.get('first_name','').strip()} {r.get('last_name','').strip()}".strip()
                patient_map[pid] = name or str(pid)
        dentist_map = {}
        if ok_den and dentist_rows:
            for r in dentist_rows:
                did = r.get("dentist_id")
                # Try common fullname field names, then fall back to first/last.
                name = (
                    r.get("fullname")
                    or r.get("full_name")
                    or r.get("name")
                    or ""
                ).strip()
                if not name:
                    name = f"{r.get('first_name','').strip()} {r.get('last_name','').strip()}".strip()
                dentist_map[did] = name or str(did)

        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        scroll.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_rowconfigure(0, weight=1)

        if not rows:
            ctk.CTkLabel(scroll, text="No appointments found.").grid(
                row=0, column=0, padx=8, pady=8, sticky="w"
            )
            return

        columns = [
            ("patient_name", "Patient", 2),
            ("dentist_name", "Dentist", 2),
            ("scheduled_at", "Scheduled at", 2),
            ("reason", "Reason", 2),
            ("status", "Status", 1),
            ("created_at", "Created", 2),
        ]
        minsize = {
            "patient_name": 200,
            "dentist_name": 200,
            "scheduled_at": 220,
            "reason": 180,
            "status": 140,
            "created_at": 200,
        }

        table = ctk.CTkFrame(
            scroll,
            corner_radius=6,
            fg_color="#ffffff",
            border_width=1,
            border_color="#e5e7eb",
        )
        table.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        table.grid_columnconfigure(tuple(range(len(columns))), weight=1)

        header_font = ctk.CTkFont(size=12, weight="bold")
        cell_font = ctk.CTkFont(size=12)

        for c_idx, (_, header, weight) in enumerate(columns):
            key = columns[c_idx][0]
            table.grid_columnconfigure(c_idx, weight=weight, minsize=minsize.get(key, 140))
            ctk.CTkLabel(
                table,
                text=header,
                font=header_font,
                text_color="#111827",
                fg_color="#f5f5f5",
            ).grid(row=0, column=c_idx, padx=4, pady=4, sticky="nsew")

        for r_idx, row in enumerate(rows, start=1):
            bg = "#ffffff" if r_idx % 2 else "#f9fafb"
            status_val = row.get("status", "")
            status_mark = "OK" if str(status_val).lower() in ("active", "confirmed", "1", "true", "yes") else str(status_val)
            patient_name = patient_map.get(row.get("patient_id"), row.get("patient_id", ""))
            dentist_name = dentist_map.get(row.get("dentist_id"), row.get("dentist_id", ""))
            values = {
                "patient_name": patient_name,
                "dentist_name": dentist_name,
                "scheduled_at": row.get("scheduled_at", ""),
                "reason": row.get("reason", ""),
                "status": status_mark,
                "created_at": row.get("created_at", ""),
            }
            for c_idx, (key, _, _) in enumerate(columns):
                ctk.CTkLabel(
                    table,
                    text=str(values.get(key, "")),
                    font=cell_font,
                    text_color="#111827",
                    anchor="w",
                    fg_color=bg,
                ).grid(row=r_idx, column=c_idx, padx=4, pady=4, sticky="nsew")
            # Bind row click to open history modal
            for child in table.grid_slaves(row=r_idx):
                child.bind("<Button-1>", lambda _e, appt=row: self._open_history_modal(appt))

    def _draw_line_chart(self, canvas: tk.Canvas, values: list[int]) -> None:
        """Draw a simple line chart for the given values."""
        w, h = int(canvas["width"]), int(canvas["height"])
        padding = 30
        min_v, max_v = min(values), max(values)
        span = max(max_v - min_v, 1)
        points = []
        for i, v in enumerate(values):
            x = padding + i * (w - 2 * padding) / max(len(values) - 1, 1)
            y = h - padding - ((v - min_v) / span) * (h - 2 * padding)
            points.append((x, y))
        canvas.create_line(padding, h - padding, w - padding, h - padding, fill="#1f2937", width=2)
        canvas.create_line(padding, padding, padding, h - padding, fill="#1f2937", width=2)
        for x, y in zip(points, points[1:]):
            canvas.create_line(x[0], x[1], y[0], y[1], fill="#0ea5e9", width=3, smooth=True)
        for x, y in points:
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#0ea5e9", outline="")

    def _draw_pie_chart(self, canvas: tk.Canvas, slices: dict[str, tuple[str, int]]) -> None:
        """Draw a simple pie chart; slices is label -> (color, value)."""
        w, h = int(canvas["width"]), int(canvas["height"])
        bbox = (10, 10, h - 10, h - 10)
        total = sum(val for _, val in slices.values()) or 1
        start = 0
        legend_y = 20
        for label, (color, val) in slices.items():
            extent = 360 * (val / total)
            canvas.create_arc(*bbox, start=start, extent=extent, fill=color, outline="#0b1220")
            canvas.create_rectangle(h + 10, legend_y - 6, h + 26, legend_y + 10, fill=color, outline="")
            canvas.create_text(h + 32, legend_y + 2, anchor="w", fill="#e5e7eb", text=f"{label} ({val})", font=("Arial", 10))
            start += extent
            legend_y += 20

    def _open_history_modal(self, appt_row: dict) -> None:
        """Modal to capture diagnosis/follow-up/notes and save to patient_history."""
        appt_id = appt_row.get("appointment_id")
        patient_id = appt_row.get("patient_id")
        sched_raw = str(appt_row.get("scheduled_at") or "")
        visit_date = ""
        if sched_raw:
            visit_date = sched_raw.split(" ")[0]

        top = ctk.CTkToplevel(self)
        top.title("Add patient history")
        top.geometry("420x380")
        top.grab_set()
        for i in range(2):
            top.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(top, text="Diagnosis").grid(row=0, column=0, padx=10, pady=(12, 4), sticky="w")
        diag_entry = ctk.CTkEntry(top, placeholder_text="Diagnosis")
        diag_entry.grid(row=0, column=1, padx=10, pady=(12, 4), sticky="ew")

        ctk.CTkLabel(top, text="Follow-up date (YYYY-MM-DD)").grid(row=1, column=0, padx=10, pady=4, sticky="w")
        follow_entry = ctk.CTkEntry(top, placeholder_text="YYYY-MM-DD")
        follow_entry.grid(row=1, column=1, padx=10, pady=4, sticky="ew")

        ctk.CTkLabel(top, text="Prescription").grid(row=2, column=0, padx=10, pady=4, sticky="w")
        rx_entry = ctk.CTkEntry(top, placeholder_text="e.g., Amoxicillin 500mg 3x/day")
        rx_entry.grid(row=2, column=1, padx=10, pady=4, sticky="ew")

        ctk.CTkLabel(top, text="Notes").grid(row=3, column=0, padx=10, pady=4, sticky="nw")
        notes_box = ctk.CTkTextbox(top, height=120)
        notes_box.grid(row=3, column=1, padx=10, pady=4, sticky="nsew")
        # Show existing notes (if any) for visibility
        existing_notes = str(appt_row.get("notes") or "").strip()
        if existing_notes:
            ctk.CTkLabel(top, text="Existing notes").grid(row=4, column=0, padx=10, pady=(4, 0), sticky="w")
            existing_box = ctk.CTkTextbox(top, height=60)
            existing_box.insert("1.0", existing_notes)
            existing_box.configure(state="disabled")
            existing_box.grid(row=4, column=1, padx=10, pady=(4, 0), sticky="nsew")

        status_lbl = ctk.CTkLabel(top, text="", text_color="orange")
        status_row = 5 if existing_notes else 4
        status_lbl.grid(row=status_row, column=0, columnspan=2, padx=10, pady=(4, 0), sticky="w")

        def save_history() -> None:
            diag = diag_entry.get().strip()
            follow = follow_entry.get().strip()
            notes = notes_box.get("1.0", "end").strip()
            rx = rx_entry.get().strip()
            treatment_given = appt_row.get("reason", "")
            if not patient_id or not appt_id:
                status_lbl.configure(text="Missing patient or appointment id.")
                return
            if not visit_date:
                status_lbl.configure(text="Missing visit date.")
                return
            ok, msg = insert_patient_history(
                patient_id=patient_id,
                appointment_id=appt_id,
                visit_date=visit_date,
                diagnosis=diag or None,
                treatment_given=treatment_given or None,
                prescription=rx or None,
                follow_up_date=follow or None,
                notes=notes or None,
            )
            if not ok:
                status_lbl.configure(text=msg)
                return
            status_lbl.configure(text="History saved.")
            top.destroy()
            # Refresh appointments view to reflect any potential changes
            self._render_appointments()

        ctk.CTkButton(
            top,
            text="Save",
            fg_color="#123055",
            hover_color="#0c2340",
            text_color="#ffffff",
            command=save_history,
        ).grid(row=status_row + 1, column=0, columnspan=2, padx=10, pady=12, sticky="ew")
