/* Alarab Logistics Platform — Frontend */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

let page = "overview";
let me = null;
let arabic = false;
let cache = { customers: [], vehicles: [], drivers: [], shipments: [], invoices: [] };

const i18n = {
  en: {
    email: "Email", password: "Password", sign_in: "Sign in", sign_out: "Sign out",
    nav_overview: "Overview", nav_shipments: "Shipments", nav_customers: "Customers",
    nav_fleet: "Fleet", nav_drivers: "Drivers", nav_invoices: "Invoices",
    nav_users: "Users", nav_audit: "Audit Log",
    heading_overview: "Business overview", heading_shipments: "Shipment management",
    heading_customers: "Customer directory", heading_fleet: "Fleet management",
    heading_drivers: "Driver management", heading_invoices: "Invoicing",
    heading_users: "User management", heading_audit: "Audit trail",
    customers: "Customers", vehicles: "Vehicles", drivers: "Drivers",
    shipments: "Shipments", active: "Active", delivered: "Delivered",
    invoices: "Invoices", pending_inv: "Pending invoices", revenue: "Paid revenue",
    available_v: "Available vehicles", available_d: "Available drivers",
    recent_activity: "Recent activity", no_activity: "No activity yet",
    add_customer: "+ Add customer", add_vehicle: "+ Add vehicle",
    add_driver: "+ Add driver", create_shipment: "+ Create shipment",
    create_invoice: "+ Create invoice", add_user: "+ Add user",
    name: "Name", phone: "Phone", city: "City", country: "Country",
    registration: "Registration", type: "Type", capacity: "Capacity (t)",
    status: "Status", license: "License No.", reference: "Reference",
    pickup: "Pickup", delivery: "Delivery", cargo: "Cargo", weight: "Weight (t)",
    vehicle: "Vehicle", driver: "Driver", amount: "Amount", currency: "Currency",
    due: "Due date", number: "Invoice No.", role: "Role", actions: "Actions",
    save: "Save", cancel: "Cancel", edit: "Edit", change_status: "Status",
    no_records: "No records yet", filter_all: "All statuses",
    search_placeholder: "Search…", full_name: "Full name", address: "Address",
    notes: "Notes", make_model: "Make / Model", scheduled: "Scheduled date",
    user: "User", action: "Action", entity: "Entity", detail: "Detail", time: "Time",
    active_user: "Active", inactive_user: "Inactive"
  },
  ar: {
    email: "البريد الإلكتروني", password: "كلمة المرور", sign_in: "تسجيل الدخول", sign_out: "تسجيل الخروج",
    nav_overview: "نظرة عامة", nav_shipments: "الشحنات", nav_customers: "العملاء",
    nav_fleet: "الأسطول", nav_drivers: "السائقون", nav_invoices: "الفواتير",
    nav_users: "المستخدمون", nav_audit: "سجل التدقيق",
    heading_overview: "نظرة عامة على الأعمال", heading_shipments: "إدارة الشحنات",
    heading_customers: "دليل العملاء", heading_fleet: "إدارة الأسطول",
    heading_drivers: "إدارة السائقين", heading_invoices: "الفواتير",
    heading_users: "إدارة المستخدمين", heading_audit: "سجل التدقيق",
    customers: "العملاء", vehicles: "المركبات", drivers: "السائقون",
    shipments: "الشحنات", active: "نشطة", delivered: "تم التسليم",
    invoices: "الفواتير", pending_inv: "فواتير معلقة", revenue: "الإيرادات المدفوعة",
    available_v: "مركبات متاحة", available_d: "سائقون متاحون",
    recent_activity: "النشاط الأخير", no_activity: "لا يوجد نشاط بعد",
    add_customer: "+ إضافة عميل", add_vehicle: "+ إضافة مركبة",
    add_driver: "+ إضافة سائق", create_shipment: "+ إنشاء شحنة",
    create_invoice: "+ إنشاء فاتورة", add_user: "+ إضافة مستخدم",
    name: "الاسم", phone: "الهاتف", city: "المدينة", country: "الدولة",
    registration: "رقم اللوحة", type: "النوع", capacity: "السعة (طن)",
    status: "الحالة", license: "رقم الرخصة", reference: "المرجع",
    pickup: "الاستلام", delivery: "التسليم", cargo: "البضاعة", weight: "الوزن (طن)",
    vehicle: "المركبة", driver: "السائق", amount: "المبلغ", currency: "العملة",
    due: "تاريخ الاستحقاق", number: "رقم الفاتورة", role: "الدور", actions: "إجراءات",
    save: "حفظ", cancel: "إلغاء", edit: "تعديل", change_status: "الحالة",
    no_records: "لا توجد سجلات بعد", filter_all: "كل الحالات",
    search_placeholder: "بحث…", full_name: "الاسم الكامل", address: "العنوان",
    notes: "ملاحظات", make_model: "الماركة / الموديل", scheduled: "التاريخ المجدول",
    user: "المستخدم", action: "الإجراء", entity: "الكيان", detail: "التفاصيل", time: "الوقت",
    active_user: "نشط", inactive_user: "غير نشط"
  }
};

function t(key) {
  return (arabic ? i18n.ar : i18n.en)[key] || key;
}

function applyI18n() {
  $$("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (i18n.en[key]) el.textContent = t(key);
  });
}

/* ─── API ─── */
async function api(path, opts = {}) {
  const r = await fetch(path, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) }
  });
  if (r.status === 401) throw new Error("Please sign in");
  let data;
  try { data = await r.json(); } catch { data = {}; }
  if (!r.ok) throw new Error(data.detail || (typeof data.detail === "string" ? data.detail : "Request failed"));
  return data;
}

/* ─── Utils ─── */
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function pill(status) {
  if (!status) return "";
  const cls = "pill-" + status.toLowerCase().replace(/\s+/g, "-");
  return `<span class="pill ${cls}">${esc(status)}</span>`;
}

function toast(msg, isError = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  el.style.background = isError ? "#991b1b" : "#0f1c27";
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.hidden = true; }, 3200);
}

function closeModal() {
  $("#modalRoot").innerHTML = "";
}

function openModal(title, fieldsHtml, onSubmit) {
  const root = $("#modalRoot");
  root.innerHTML = `
    <div class="modal-backdrop" id="modalBackdrop">
      <div class="modal" role="dialog">
        <div class="modal-header">
          <h3>${esc(title)}</h3>
          <button class="modal-close" type="button" aria-label="Close">&times;</button>
        </div>
        <div class="modal-body">
          <form id="modalForm">
            ${fieldsHtml}
            <div class="modal-actions">
              <button type="button" class="btn btn-secondary" id="modalCancel">${t("cancel")}</button>
              <button type="submit" class="btn btn-primary">${t("save")}</button>
            </div>
          </form>
        </div>
      </div>
    </div>`;
  $("#modalBackdrop").onclick = e => { if (e.target.id === "modalBackdrop") closeModal(); };
  $(".modal-close", root).onclick = closeModal;
  $("#modalCancel", root).onclick = closeModal;
  $("#modalForm", root).onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = Object.fromEntries(fd.entries());
    // Convert numbers
    for (const k of ["amount", "capacity_tonnes", "weight_tonnes", "customer_id", "vehicle_id", "driver_id", "shipment_id"]) {
      if (data[k] !== undefined && data[k] !== "") data[k] = Number(data[k]);
      if (data[k] === "") delete data[k];
    }
    try {
      await onSubmit(data);
      closeModal();
    } catch (err) {
      toast(err.message, true);
    }
  };
}

function table(headers, rows) {
  return `<div class="table-wrap"><table>
    <thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
    <tbody>${rows.length
      ? rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")
      : `<tr><td colspan="${headers.length}" class="empty">${t("no_records")}</td></tr>`
    }</tbody>
  </table></div>`;
}

function section(title, actionsHtml = "") {
  return `<div class="panel"><div class="panel-head"><h3>${title}</h3><div class="toolbar">${actionsHtml}</div></div><div class="panel-body">`;
}

/* ─── Pages ─── */
async function renderOverview() {
  const s = await api("/api/summary");
  const metrics = [
    [t("customers"), s.customers, ""],
    [t("vehicles"), s.vehicles, `${s.available_vehicles} ${t("available_v").toLowerCase()}`],
    [t("drivers"), s.drivers, `${s.available_drivers} ${t("available_d").toLowerCase()}`],
    [t("shipments"), s.shipments, `${s.active_shipments} ${t("active").toLowerCase()}`],
    [t("delivered"), s.delivered_shipments, ""],
    [t("invoices"), s.invoices, `${s.pending_invoices} ${t("pending_inv").toLowerCase()}`],
    [t("revenue"), s.paid_revenue.toLocaleString(), "SAR / BHD"],
  ];

  let html = `<div class="metrics">${metrics.map(([label, val, sub]) =>
    `<div class="metric-card"><div class="label">${label}</div><div class="value">${val}</div>${sub ? `<div class="sub">${sub}</div>` : ""}</div>`
  ).join("")}</div>`;

  html += `<div class="panel"><div class="panel-head"><h3>${t("recent_activity")}</h3></div><div class="panel-body">`;
  if (s.recent_activity?.length) {
    html += `<ul class="activity-list">${s.recent_activity.map(a =>
      `<li><div class="activity-dot"></div><div>
        <div><strong>${esc(a.user)}</strong> · ${esc(a.action)} ${esc(a.entity)}${a.detail ? ` — ${esc(a.detail)}` : ""}</div>
        <div class="activity-meta">${esc(a.at?.replace("T", " ").slice(0, 19) || "")}</div>
      </div></li>`
    ).join("")}</ul>`;
  } else {
    html += `<p class="empty">${t("no_activity")}</p>`;
  }
  html += `</div></div>`;
  return html;
}

async function renderCustomers() {
  const q = "";
  cache.customers = await api("/api/customers" + (q ? `?q=${encodeURIComponent(q)}` : ""));
  const rows = cache.customers.map(c => [
    esc(c.name),
    esc(c.email) || "—",
    esc(c.phone) || "—",
    esc(c.city) || "—",
    esc(c.country) || "—",
    `<button class="btn-link" onclick="editCustomer(${c.id})">${t("edit")}</button>`
  ]);
  return section(t("nav_customers"),
    `<button class="btn btn-primary" onclick="openCustomerModal()">${t("add_customer")}</button>`
  ) + table([t("name"), t("email"), t("phone"), t("city"), t("country"), t("actions")], rows) + "</div></div>";
}

async function renderFleet() {
  cache.vehicles = await api("/api/vehicles");
  const rows = cache.vehicles.map(v => [
    `<strong>${esc(v.registration)}</strong>`,
    esc(v.vehicle_type),
    esc(v.make_model) || "—",
    v.capacity_tonnes || "—",
    pill(v.status),
    `<button class="btn-link" onclick="editVehicle(${v.id})">${t("edit")}</button>`
  ]);
  return section(t("nav_fleet"),
    `<button class="btn btn-primary" onclick="openVehicleModal()">${t("add_vehicle")}</button>`
  ) + table([t("registration"), t("type"), t("make_model"), t("capacity"), t("status"), t("actions")], rows) + "</div></div>";
}

async function renderDrivers() {
  cache.drivers = await api("/api/drivers");
  const rows = cache.drivers.map(d => [
    esc(d.full_name),
    esc(d.phone) || "—",
    esc(d.license_no) || "—",
    pill(d.status),
    `<button class="btn-link" onclick="editDriver(${d.id})">${t("edit")}</button>`
  ]);
  return section(t("nav_drivers"),
    `<button class="btn btn-primary" onclick="openDriverModal()">${t("add_driver")}</button>`
  ) + table([t("full_name"), t("phone"), t("license"), t("status"), t("actions")], rows) + "</div></div>";
}

async function renderShipments() {
  cache.shipments = await api("/api/shipments");
  cache.vehicles = cache.vehicles.length ? cache.vehicles : await api("/api/vehicles");
  cache.drivers = cache.drivers.length ? cache.drivers : await api("/api/drivers");
  cache.customers = cache.customers.length ? cache.customers : await api("/api/customers");

  const rows = cache.shipments.map(s => [
    `<strong>${esc(s.reference)}</strong>`,
    esc(s.customer),
    esc(s.pickup) || "—",
    esc(s.delivery) || "—",
    esc(s.cargo) || "—",
    s.weight_tonnes || "—",
    esc(s.vehicle) || "—",
    esc(s.driver) || "—",
    pill(s.status),
    `<button class="btn-link" onclick="openStatusModal('shipment',${s.id},'${esc(s.status)}')">${t("change_status")}</button>`
  ]);
  return section(t("nav_shipments"),
    `<button class="btn btn-primary" onclick="openShipmentModal()">${t("create_shipment")}</button>`
  ) + table([t("reference"), t("name"), t("pickup"), t("delivery"), t("cargo"), t("weight"), t("vehicle"), t("driver"), t("status"), t("actions")], rows) + "</div></div>";
}

async function renderInvoices() {
  cache.invoices = await api("/api/invoices");
  const rows = cache.invoices.map(i => [
    `<strong>${esc(i.number)}</strong>`,
    esc(i.customer),
    Number(i.amount).toLocaleString(undefined, { minimumFractionDigits: 2 }),
    esc(i.currency),
    pill(i.status),
    esc(i.due_date) || "—",
    `<button class="btn-link" onclick="openStatusModal('invoice',${i.id},'${esc(i.status)}')">${t("change_status")}</button>`
  ]);
  return section(t("nav_invoices"),
    `<button class="btn btn-primary" onclick="openInvoiceModal()">${t("create_invoice")}</button>`
  ) + table([t("number"), t("name"), t("amount"), t("currency"), t("status"), t("due"), t("actions")], rows) + "</div></div>";
}

async function renderUsers() {
  const users = await api("/api/users");
  const rows = users.map(u => [
    esc(u.email),
    esc(u.full_name) || "—",
    esc(u.role),
    u.active ? `<span class="pill pill-available">${t("active_user")}</span>` : `<span class="pill pill-cancelled">${t("inactive_user")}</span>`,
    ""
  ]);
  return section(t("nav_users"),
    `<button class="btn btn-primary" onclick="openUserModal()">${t("add_user")}</button>`
  ) + table([t("email"), t("full_name"), t("role"), t("status"), ""], rows) + "</div></div>";
}

async function renderAudit() {
  const logs = await api("/api/audit");
  const rows = logs.map(l => [
    esc(l.user),
    esc(l.action),
    esc(l.entity) + (l.entity_id ? ` #${l.entity_id}` : ""),
    esc(l.detail) || "—",
    esc(l.created_at?.replace("T", " ").slice(0, 19) || "")
  ]);
  return section(t("nav_audit")) + table([t("user"), t("action"), t("entity"), t("detail"), t("time")], rows) + "</div></div>";
}

/* ─── Modals ─── */
window.openCustomerModal = (existing = null) => {
  const f = existing || {};
  openModal(existing ? t("edit") + " " + t("nav_customers") : t("add_customer"), `
    <label>${t("name")}</label><input name="name" required value="${esc(f.name || "")}">
    <label>${t("email")}</label><input name="email" type="email" value="${esc(f.email || "")}">
    <label>${t("phone")}</label><input name="phone" value="${esc(f.phone || "")}">
    <label>${t("address")}</label><input name="address" value="${esc(f.address || "")}">
    <label>${t("city")}</label><input name="city" value="${esc(f.city || "")}">
    <label>${t("country")}</label><input name="country" value="${esc(f.country || "Saudi Arabia")}">
    <label>${t("notes")}</label><textarea name="notes">${esc(f.notes || "")}</textarea>
  `, async data => {
    if (existing) await api(`/api/customers/${existing.id}`, { method: "PUT", body: JSON.stringify(data) });
    else await api("/api/customers", { method: "POST", body: JSON.stringify(data) });
    toast("Saved");
    render();
  });
};

window.editCustomer = id => {
  const c = cache.customers.find(x => x.id === id);
  if (c) openCustomerModal(c);
};

window.openVehicleModal = (existing = null) => {
  const f = existing || {};
  openModal(existing ? t("edit") : t("add_vehicle"), `
    <label>${t("registration")}</label><input name="registration" required value="${esc(f.registration || "")}">
    <label>${t("type")}</label>
    <select name="vehicle_type">
      ${["Truck","Trailer","Flatbed","Reefer","Tank","Van"].map(t =>
        `<option ${f.vehicle_type === t ? "selected" : ""}>${t}</option>`).join("")}
    </select>
    <label>${t("make_model")}</label><input name="make_model" value="${esc(f.make_model || "")}">
    <label>${t("capacity")}</label><input name="capacity_tonnes" type="number" step="0.1" value="${f.capacity_tonnes || 0}">
    <label>${t("status")}</label>
    <select name="status">
      ${["Available","In Use","Maintenance"].map(s =>
        `<option ${f.status === s ? "selected" : ""}>${s}</option>`).join("")}
    </select>
    <label>${t("notes")}</label><textarea name="notes">${esc(f.notes || "")}</textarea>
  `, async data => {
    if (existing) await api(`/api/vehicles/${existing.id}`, { method: "PUT", body: JSON.stringify(data) });
    else await api("/api/vehicles", { method: "POST", body: JSON.stringify(data) });
    toast("Saved");
    render();
  });
};

window.editVehicle = id => {
  const v = cache.vehicles.find(x => x.id === id);
  if (v) openVehicleModal(v);
};

window.openDriverModal = (existing = null) => {
  const f = existing || {};
  openModal(existing ? t("edit") : t("add_driver"), `
    <label>${t("full_name")}</label><input name="full_name" required value="${esc(f.full_name || "")}">
    <label>${t("phone")}</label><input name="phone" value="${esc(f.phone || "")}">
    <label>${t("license")}</label><input name="license_no" value="${esc(f.license_no || "")}">
    <label>${t("status")}</label>
    <select name="status">
      ${["Available","On Trip","Off Duty"].map(s =>
        `<option ${f.status === s ? "selected" : ""}>${s}</option>`).join("")}
    </select>
    <label>${t("notes")}</label><textarea name="notes">${esc(f.notes || "")}</textarea>
  `, async data => {
    if (existing) await api(`/api/drivers/${existing.id}`, { method: "PUT", body: JSON.stringify(data) });
    else await api("/api/drivers", { method: "POST", body: JSON.stringify(data) });
    toast("Saved");
    render();
  });
};

window.editDriver = id => {
  const d = cache.drivers.find(x => x.id === id);
  if (d) openDriverModal(d);
};

window.openShipmentModal = () => {
  const custOpts = cache.customers.map(c => `<option value="${esc(c.name)}" data-id="${c.id}">${esc(c.name)}</option>`).join("");
  const vehOpts = `<option value="">—</option>` + cache.vehicles.filter(v => v.status === "Available").map(v =>
    `<option value="${v.id}">${esc(v.registration)} (${esc(v.vehicle_type)})</option>`).join("");
  const drvOpts = `<option value="">—</option>` + cache.drivers.filter(d => d.status === "Available").map(d =>
    `<option value="${d.id}">${esc(d.full_name)}</option>`).join("");

  openModal(t("create_shipment"), `
    <label>${t("name")}</label>
    <input name="customer" list="custList" required>
    <datalist id="custList">${custOpts}</datalist>
    <label>${t("pickup")}</label><input name="pickup">
    <label>${t("delivery")}</label><input name="delivery">
    <label>${t("cargo")}</label><input name="cargo">
    <label>${t("weight")}</label><input name="weight_tonnes" type="number" step="0.1" value="0">
    <label>${t("vehicle")}</label><select name="vehicle_id">${vehOpts}</select>
    <label>${t("driver")}</label><select name="driver_id">${drvOpts}</select>
    <label>${t("scheduled")}</label><input name="scheduled_date" type="date">
    <label>${t("notes")}</label><textarea name="notes"></textarea>
  `, async data => {
    const match = cache.customers.find(c => c.name === data.customer);
    if (match) data.customer_id = match.id;
    if (!data.vehicle_id) delete data.vehicle_id;
    if (!data.driver_id) delete data.driver_id;
    const res = await api("/api/shipments", { method: "POST", body: JSON.stringify(data) });
    toast(`Shipment ${res.reference} created`);
    render();
  });
};

window.openInvoiceModal = () => {
  const custOpts = cache.customers.map(c => `<option value="${esc(c.name)}">${esc(c.name)}</option>`).join("");
  openModal(t("create_invoice"), `
    <label>${t("name")}</label>
    <input name="customer" list="custList2" required>
    <datalist id="custList2">${custOpts}</datalist>
    <label>${t("amount")}</label><input name="amount" type="number" step="0.01" min="0.01" required>
    <label>${t("currency")}</label>
    <select name="currency"><option>SAR</option><option>BHD</option><option>USD</option><option>AED</option></select>
    <label>${t("due")}</label><input name="due_date" type="date">
    <label>${t("notes")}</label><textarea name="notes"></textarea>
  `, async data => {
    const match = cache.customers.find(c => c.name === data.customer);
    if (match) data.customer_id = match.id;
    const res = await api("/api/invoices", { method: "POST", body: JSON.stringify(data) });
    toast(`Invoice ${res.number} created`);
    render();
  });
};

window.openUserModal = () => {
  openModal(t("add_user"), `
    <label>${t("email")}</label><input name="email" type="email" required>
    <label>${t("password")}</label><input name="password" type="password" required minlength="8">
    <label>${t("full_name")}</label><input name="full_name">
    <label>${t("role")}</label>
    <select name="role">
      ${["Operations","Transport Manager","Sales Manager","Finance Manager","Accountant","MD","Admin"].map(r =>
        `<option>${r}</option>`).join("")}
    </select>
  `, async data => {
    await api("/api/users", { method: "POST", body: JSON.stringify(data) });
    toast("User created");
    render();
  });
};

window.openStatusModal = (kind, id, current) => {
  const shipmentStatuses = ["Pending", "Confirmed", "In Transit", "Delivered", "Cancelled"];
  const invoiceStatuses = ["Draft", "Sent", "Paid", "Overdue", "Cancelled"];
  const opts = (kind === "shipment" ? shipmentStatuses : invoiceStatuses)
    .map(s => `<option ${s === current ? "selected" : ""}>${s}</option>`).join("");

  openModal(t("change_status"), `
    <label>${t("status")}</label>
    <select name="status">${opts}</select>
  `, async data => {
    const path = kind === "shipment" ? `/api/shipments/${id}/status` : `/api/invoices/${id}/status`;
    await api(path, { method: "PUT", body: JSON.stringify(data) });
    toast("Status updated");
    render();
  });
};

/* ─── Core render ─── */
const titles = {
  overview: "heading_overview", shipments: "heading_shipments", customers: "heading_customers",
  fleet: "heading_fleet", drivers: "heading_drivers", invoices: "heading_invoices",
  users: "heading_users", audit: "heading_audit"
};

async function render() {
  const headingKey = titles[page] || "heading_overview";
  $("#heading").textContent = t(headingKey);
  $("#crumb").textContent = page.toUpperCase();

  // Admin-only nav
  const isAdmin = me && (me.role === "Admin" || me.role === "MD");
  $$(".admin-only").forEach(el => el.style.display = isAdmin ? "" : "none");

  let html = "";
  try {
    if (page === "overview") html = await renderOverview();
    else if (page === "customers") html = await renderCustomers();
    else if (page === "fleet") html = await renderFleet();
    else if (page === "drivers") html = await renderDrivers();
    else if (page === "shipments") html = await renderShipments();
    else if (page === "invoices") html = await renderInvoices();
    else if (page === "users") html = await renderUsers();
    else if (page === "audit") html = await renderAudit();
  } catch (e) {
    html = `<div class="panel"><div class="panel-body"><p class="empty">${esc(e.message)}</p></div></div>`;
    if (e.message.includes("Sign in")) location.reload();
  }
  $("#content").innerHTML = html;
}

/* ─── Boot ─── */
async function start() {
  try {
    me = await api("/api/me");
    $("#login").style.display = "none";
    $("#app").hidden = false;
    $("#userEmail").textContent = me.full_name || me.email;
    $("#userRole").textContent = me.role;
    render();
  } catch {
    $("#login").style.display = "grid";
  }
}

$$(".nav-item").forEach(btn => {
  btn.onclick = () => {
    page = btn.dataset.page;
    $$(".nav-item").forEach(x => x.classList.toggle("active", x === btn));
    render();
  };
});

$("#langBtn").onclick = () => {
  arabic = !arabic;
  document.documentElement.dir = arabic ? "rtl" : "ltr";
  document.documentElement.lang = arabic ? "ar" : "en";
  $("#langBtn").textContent = arabic ? "English" : "العربية";
  applyI18n();
  render();
};

function updateClock() {
  const el = $("#clock");
  if (el) el.textContent = new Date().toLocaleString(arabic ? "ar-SA" : "en-GB", {
    weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
  });
}
setInterval(updateClock, 30000);
updateClock();

start();
