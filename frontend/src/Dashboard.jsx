import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  ArrowDownLeft,
  ArrowUpRight,
  Users,
  CalendarDays,
  Receipt,
  LogOut,
  Plus,
  X,
  RefreshCw,
  Wallet,
  TrendingUp,
  UserRound,
  MapPin,
  ChevronDown,
  ShieldCheck,
  UserPlus,
  Search,
} from "lucide-react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";

import api from "./api";

const formatMoney = (value) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));

const today = new Date().toISOString().slice(0, 10);
const currentTime = new Date().toTimeString().slice(0, 5);

function StatCard({ title, value, icon: Icon, type, delay }) {
  return (
    <motion.div
      className={`stat-card ${type}`}
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay }}
      whileHover={{ y: -4 }}
    >
      <div className="stat-top">
        <div className="stat-icon">
          <Icon size={20} />
        </div>
      </div>

      <p>{title}</p>

      <h2>{formatMoney(value)}</h2>

      <div className="stat-line" />
    </motion.div>
  );
}

function Modal({ title, children, onClose }) {
  return (
    <AnimatePresence>
      <motion.div
        className="modal-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onMouseDown={onClose}
      >
        <motion.div
          className="modal-card"
          initial={{ opacity: 0, scale: 0.96, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 20 }}
          transition={{ duration: 0.2 }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div className="modal-header">
            <div>
              <h2>{title}</h2>
              <p>Add information to your pandal records.</p>
            </div>

            <button className="icon-button" onClick={onClose}>
              <X size={20} />
            </button>
          </div>

          {children}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function Dashboard() {
  const [user, setUser] = useState(null);
  const [pandal, setPandal] = useState(null);
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [members, setMembers] = useState([]);
  const [events, setEvents] = useState([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [activeSection, setActiveSection] = useState("overview");
  const [modal, setModal] = useState(null);

  const [incomeForm, setIncomeForm] = useState({
    category: "sponsor",
    source_name: "",
    amount: "",
    payment_method: "upi",
    transaction_reference: "",
    transaction_date: today,
    transaction_time: currentTime,
    proof_url: "",
    proof_file: null,
    received_by: "",
    notes: "",
  });

  const [expenseForm, setExpenseForm] = useState({
    expense_type: "item",
    item_name: "",
    amount: "",
    spent_by: "",
    payment_method: "cash",
    expense_date: today,
    expense_time: currentTime,
    proof_url: "",
    proof_file: null,
    notes: "",
    cash_details: {
      given_to: "",
      given_date: today,
      given_time: currentTime,
      location: "",
      organiser_known: true,
      purpose: "",
    },
  });

  const [eventForm, setEventForm] = useState({
    event_name: "",
    planned_budget: "",
    budget_arranged: false,
    description: "",
  });

  const role = pandal?.role;
  const canManageMoney = role === "admin" || role === "cashier";
  const isOrganiser = role === "admin";

  const loadData = async (showRefresh = false) => {
    try {
      setError("");

      if (showRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const meResponse = await api.get("/auth/me");
      setUser(meResponse.data);

      const pandalsResponse = await api.get("/pandals");

      if (!pandalsResponse.data.length) {
        throw new Error("No Pandal found for this account.");
      }

      const selectedPandal = pandalsResponse.data[0];
      setPandal(selectedPandal);

      const [
        dashboardResponse,
        transactionResponse,
        memberResponse,
        eventResponse,
      ] = await Promise.all([
        api.get(`/pandals/${selectedPandal.id}/dashboard`),
        api.get(`/pandals/${selectedPandal.id}/transactions`),
        api.get(`/pandals/${selectedPandal.id}/members`),
        api.get(`/pandals/${selectedPandal.id}/events`),
      ]);

      setSummary(dashboardResponse.data);
      setTransactions(transactionResponse.data);
      setMembers(memberResponse.data);
      setEvents(eventResponse.data);

      setIncomeForm((previous) => ({
        ...previous,
        received_by: previous.received_by || meResponse.data.id,
      }));

      setExpenseForm((previous) => ({
        ...previous,
        spent_by: previous.spent_by || meResponse.data.id,
      }));
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load dashboard.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const logout = () => {
    localStorage.clear();
    window.location.href = "/login";
  };

  const submitIncome = async (e) => {
    e.preventDefault();

    if (!incomeForm.proof_file) {
      alert("Please upload the transaction proof image.");
      return;
    }

    try {
      // 1. Upload proof image
      const formData = new FormData();
      formData.append("file", incomeForm.proof_file);
      console.log("Proof file:", incomeForm.proof_file);
      console.log("FormData file:", formData.get("file"));

      const uploadResponse = await api.post("/uploads/proof", formData);

      const proofUrl = uploadResponse.data.proof_url;

      // 2. Save income transaction
      await api.post(`/pandals/${pandal.id}/income`, {
        category: incomeForm.category,
        source_name: incomeForm.source_name,
        amount: Number(incomeForm.amount),
        payment_method: incomeForm.payment_method,
        transaction_reference: incomeForm.transaction_reference,
        transaction_date: incomeForm.transaction_date,
        transaction_time: incomeForm.transaction_time,
        proof_url: proofUrl,
        received_by: incomeForm.received_by || user.id,
        notes: incomeForm.notes,
      });

      setModal(null);

      setIncomeForm({
        category: "sponsor",
        source_name: "",
        amount: "",
        payment_method: "upi",
        transaction_reference: "",
        transaction_date: today,
        transaction_time: currentTime,
        proof_url: "",
        proof_file: null,
        received_by: user.id,
        notes: "",
      });

      await loadData(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Unable to add income.");
    }
  };

  const submitExpense = async (e) => {
    e.preventDefault();

    if (!expenseForm.proof_file) {
      alert("Please upload the transaction proof image.");
      return;
    }

    try {
      // 1. Upload proof image
      const formData = new FormData();
      formData.append("file", expenseForm.proof_file);

      const uploadResponse = await api.post("/uploads/proof", formData);

      const proofUrl = uploadResponse.data.proof_url;

      // 2. Prepare expense payload
      const payload = {
        expense_type: expenseForm.expense_type,
        item_name: expenseForm.item_name,
        amount: Number(expenseForm.amount),
        spent_by: expenseForm.spent_by || user.id,
        payment_method: expenseForm.payment_method,
        expense_date: expenseForm.expense_date,
        expense_time: expenseForm.expense_time,
        proof_url: proofUrl,
        notes: expenseForm.notes,
      };

      if (expenseForm.payment_method === "cash") {
        payload.cash_details = expenseForm.cash_details;
      }

      // 3. Save expense
      await api.post(`/pandals/${pandal.id}/expenses`, payload);

      setModal(null);

      setExpenseForm({
        expense_type: "item",
        item_name: "",
        amount: "",
        spent_by: user.id,
        payment_method: "cash",
        expense_date: today,
        expense_time: currentTime,
        proof_url: "",
        proof_file: null,
        notes: "",
        cash_details: {
          given_to: "",
          given_date: today,
          given_time: currentTime,
          location: "",
          organiser_known: true,
          purpose: "",
        },
      });

      await loadData(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Unable to add expense.");
    }
  };

  const submitEvent = async (e) => {
    e.preventDefault();

    try {
      await api.post(`/pandals/${pandal.id}/events`, {
        ...eventForm,
        planned_budget: Number(eventForm.planned_budget),
      });

      setModal(null);

      setEventForm({
        event_name: "",
        planned_budget: "",
        budget_arranged: false,
        description: "",
      });

      await loadData(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Unable to create event.");
    }
  };

  const chartData = useMemo(() => {
    if (!summary) return [];

    return [
      {
        name: "Sponsors",
        value: Number(summary.income_breakdown?.sponsor || 0),
      },
      {
        name: "Chanda",
        value: Number(summary.income_breakdown?.chanda || 0),
      },
      {
        name: "Committee",
        value: Number(summary.income_breakdown?.committee_member || 0),
      },
      {
        name: "Other",
        value: Number(summary.income_breakdown?.other || 0),
      },
    ].filter((item) => item.value > 0);
  }, [summary]);

  const expenseChartData = useMemo(() => {
    if (!summary) return [];

    return [
      {
        name: "Items",
        value: Number(summary.expense_breakdown?.item || 0),
      },
      {
        name: "Events",
        value: Number(summary.expense_breakdown?.event || 0),
      },
    ].filter((item) => item.value > 0);
  }, [summary]);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-logo">
          <Wallet size={28} />
        </div>

        <div className="loading-spinner" />

        <p>Preparing your dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="loading-screen">
        <div className="error-panel">
          <ShieldCheck size={30} />
          <h2>Something went wrong</h2>
          <p>{error}</p>

          <button className="primary-button" onClick={() => loadData()}>
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-layout">
      {/* SIDEBAR */}

      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Wallet size={21} />
          </div>

          <div>
            <strong>Pandal</strong>
            <span>Budget Manager</span>
          </div>
        </div>

        <div className="sidebar-section-title">WORKSPACE</div>

        <nav>
          <button
            className={
              activeSection === "overview" ? "nav-item active" : "nav-item"
            }
            onClick={() => setActiveSection("overview")}
          >
            <LayoutDashboard size={18} />
            Overview
          </button>

          <button
            className={
              activeSection === "transactions" ? "nav-item active" : "nav-item"
            }
            onClick={() => setActiveSection("transactions")}
          >
            <Receipt size={18} />
            Transactions
          </button>

          <button
            className={
              activeSection === "members" ? "nav-item active" : "nav-item"
            }
            onClick={() => setActiveSection("members")}
          >
            <Users size={18} />
            Committee
          </button>

          {isOrganiser && (
            <button
              className={
                activeSection === "invite" ? "nav-item active" : "nav-item"
              }
              onClick={() => setActiveSection("invite")}
            >
              <UserPlus size={18} />
              Invite Members
            </button>
          )}

          <button
            className={
              activeSection === "events" ? "nav-item active" : "nav-item"
            }
            onClick={() => setActiveSection("events")}
          >
            <CalendarDays size={18} />
            Events
          </button>
        </nav>

        <div className="sidebar-spacer" />

        <div className="sidebar-user">
          <div className="avatar">
            {(user?.full_name || "U").charAt(0).toUpperCase()}
          </div>

          <div className="sidebar-user-info">
            <strong>{user?.full_name}</strong>
            <span>
              {role === "admin"
                ? "Organiser"
                : role === "cashier"
                  ? "Cashier"
                  : "Viewer"}
            </span>
          </div>

          <button className="logout-button" onClick={logout} title="Logout">
            <LogOut size={17} />
          </button>
        </div>
      </aside>

      {/* MAIN */}

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              Workspace <span>/</span> {pandal?.name}
            </div>

            <h1>
              {activeSection === "overview"
                ? "Financial Overview"
                : activeSection === "transactions"
                  ? "Transactions"
                  : activeSection === "members"
                    ? "Committee Members"
                    : activeSection === "invite"
                      ? "Invite Committee Members"
                      : "Events"}
            </h1>
          </div>

          <div className="topbar-actions">
            <button
              className="refresh-button"
              onClick={() => loadData(true)}
              disabled={refreshing}
            >
              <RefreshCw size={17} className={refreshing ? "spin" : ""} />
            </button>

            {canManageMoney && (
              <button
                className="quick-income"
                onClick={() => setModal("income")}
              >
                <Plus size={17} />
                Add Income
              </button>
            )}
          </div>
        </header>

        {activeSection === "overview" && (
          <>
            <motion.div
              className="welcome-banner"
              initial={{
                opacity: 0,
                y: 12,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
            >
              <div>
                <div className="welcome-label">{pandal?.year} FESTIVAL</div>

                <h2>Good evening, {user?.full_name?.split(" ")[0]} 👋</h2>

                <p>Here's your pandal's financial overview for today.</p>
              </div>

              <div className="welcome-balance">
                <span>Available balance</span>
                <strong>{formatMoney(summary?.remaining_budget)}</strong>
              </div>
            </motion.div>

            <section className="stats-grid">
              <StatCard
                title="Total Collected"
                value={summary?.total_received}
                icon={ArrowDownLeft}
                type="income"
                delay={0.1}
              />

              <StatCard
                title="Total Spent"
                value={summary?.total_spent}
                icon={ArrowUpRight}
                type="expense"
                delay={0.16}
              />

              <StatCard
                title="Remaining Budget"
                value={summary?.remaining_budget}
                icon={Wallet}
                type="balance"
                delay={0.22}
              />

              <StatCard
                title="Committee Members"
                value={members.length}
                icon={Users}
                type="members"
                delay={0.28}
              />
            </section>

            <section className="dashboard-grid">
              <motion.div
                className="panel chart-panel"
                initial={{
                  opacity: 0,
                  y: 15,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                transition={{
                  delay: 0.3,
                }}
              >
                <div className="panel-header">
                  <div>
                    <h3>Income distribution</h3>
                    <p>Where the collected budget is coming from</p>
                  </div>

                  <ArrowDownLeft size={20} />
                </div>

                <div className="donut-container">
                  {chartData.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={chartData}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={65}
                          outerRadius={92}
                          paddingAngle={5}
                        >
                          {chartData.map((_, index) => (
                            <Cell
                              key={index}
                              fill={
                                ["#8b5cf6", "#06b6d4", "#22c55e", "#f59e0b"][
                                  index % 4
                                ]
                              }
                            />
                          ))}
                        </Pie>

                        <Tooltip formatter={(value) => formatMoney(value)} />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="empty-chart">No income data yet</div>
                  )}
                </div>

                <div className="legend">
                  {chartData.map((item, index) => (
                    <div key={item.name}>
                      <span className={`legend-dot income-${index}`} />
                      {item.name}
                      <strong>{formatMoney(item.value)}</strong>
                    </div>
                  ))}
                </div>
              </motion.div>

              <motion.div
                className="panel chart-panel"
                initial={{
                  opacity: 0,
                  y: 15,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                transition={{
                  delay: 0.36,
                }}
              >
                <div className="panel-header">
                  <div>
                    <h3>Spending split</h3>
                    <p>How the budget is being used</p>
                  </div>
                </div>

                <div className="donut-container">
                  {expenseChartData.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={expenseChartData}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={65}
                          outerRadius={92}
                          paddingAngle={5}
                        >
                          {expenseChartData.map((_, index) => (
                            <Cell
                              key={index}
                              fill={index === 0 ? "#06b6d4" : "#f59e0b"}
                            />
                          ))}
                        </Pie>

                        <Tooltip formatter={(value) => formatMoney(value)} />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="empty-chart">No expenses yet</div>
                  )}
                </div>

                <div className="legend">
                  {expenseChartData.map((item, index) => (
                    <div key={item.name}>
                      <span
                        className={
                          index === 0 ? "legend-dot cyan" : "legend-dot orange"
                        }
                      />
                      {item.name}
                      <strong>{formatMoney(item.value)}</strong>
                    </div>
                  ))}
                </div>
              </motion.div>
            </section>

            <RecentTransactions
              transactions={transactions}
              members={members}
              onViewAll={() => setActiveSection("transactions")}
            />
          </>
        )}

        {activeSection === "transactions" && (
          <Transactions transactions={transactions} members={members} />
        )}

        {activeSection === "members" && <Members members={members} />}

        {activeSection === "invite" && isOrganiser && (
          <InviteMembers pandal={pandal} />
        )}

        {activeSection === "events" && (
          <Events
            events={events}
            isOrganiser={isOrganiser}
            onAdd={() => setModal("event")}
          />
        )}
      </main>

      {/* FLOATING ACTIONS */}

      {canManageMoney && (
        <div className="floating-actions">
          <button
            onClick={() => setModal("expense")}
            className="floating-expense"
          >
            <ArrowUpRight size={18} />
            Add Expense
          </button>

          <button
            onClick={() => setModal("income")}
            className="floating-income"
          >
            <ArrowDownLeft size={18} />
            Add Income
          </button>
        </div>
      )}

      {/* MODALS */}

      {modal === "income" && (
        <Modal title="Add income" onClose={() => setModal(null)}>
          <form className="modal-form" onSubmit={submitIncome}>
            <div className="form-grid">
              <FormInput
                label="Source name"
                value={incomeForm.source_name}
                onChange={(value) =>
                  setIncomeForm({
                    ...incomeForm,
                    source_name: value,
                  })
                }
                placeholder="ABC Traders"
                required
              />

              <FormInput
                label="Amount"
                type="number"
                value={incomeForm.amount}
                onChange={(value) =>
                  setIncomeForm({
                    ...incomeForm,
                    amount: value,
                  })
                }
                placeholder="10000"
                required
              />

              <FormSelect
                label="Category"
                value={incomeForm.category}
                onChange={(value) =>
                  setIncomeForm({
                    ...incomeForm,
                    category: value,
                  })
                }
                options={[
                  ["sponsor", "Sponsor"],
                  ["chanda", "Chanda"],
                  ["committee_member", "Committee Member"],
                  ["other", "Other"],
                ]}
              />

              <FormSelect
                label="Payment method"
                value={incomeForm.payment_method}
                onChange={(value) =>
                  setIncomeForm({
                    ...incomeForm,
                    payment_method: value,
                  })
                }
                options={[
                  ["cash", "Cash"],
                  ["upi", "UPI"],
                  ["bank_transfer", "Bank Transfer"],
                  ["cheque", "Cheque"],
                  ["other", "Other"],
                ]}
              />

              <FormInput
                label="Date"
                type="date"
                value={incomeForm.transaction_date}
                onChange={(value) =>
                  setIncomeForm({
                    ...incomeForm,
                    transaction_date: value,
                  })
                }
                required
              />

              <FormInput
                label="Time"
                type="time"
                value={incomeForm.transaction_time}
                onChange={(value) =>
                  setIncomeForm({
                    ...incomeForm,
                    transaction_time: value,
                  })
                }
                required
              />
            </div>

            <div className="form-field">
              <label>Transaction proof</label>

              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(e) =>
                  setIncomeForm({
                    ...incomeForm,
                    proof_file: e.target.files?.[0] || null,
                  })
                }
                required
              />

              {incomeForm.proof_file && (
                <div className="file-selected">
                  <span>{incomeForm.proof_file.name}</span>

                  <small>
                    {(incomeForm.proof_file.size / 1024 / 1024).toFixed(2)} MB
                  </small>
                </div>
              )}
            </div>

            <FormInput
              label="Transaction reference"
              value={incomeForm.transaction_reference}
              onChange={(value) =>
                setIncomeForm({
                  ...incomeForm,
                  transaction_reference: value,
                })
              }
              placeholder="UPI reference / cheque number"
            />

            <FormTextarea
              label="Notes"
              value={incomeForm.notes}
              onChange={(value) =>
                setIncomeForm({
                  ...incomeForm,
                  notes: value,
                })
              }
            />

            <button className="primary-button">Save income</button>
          </form>
        </Modal>
      )}

      {modal === "expense" && (
        <Modal title="Add expense" onClose={() => setModal(null)}>
          <form className="modal-form" onSubmit={submitExpense}>
            <div className="form-grid">
              <FormInput
                label="Item / expense name"
                value={expenseForm.item_name}
                onChange={(value) =>
                  setExpenseForm({
                    ...expenseForm,
                    item_name: value,
                  })
                }
                placeholder="Decoration materials"
                required
              />

              <FormInput
                label="Amount"
                type="number"
                value={expenseForm.amount}
                onChange={(value) =>
                  setExpenseForm({
                    ...expenseForm,
                    amount: value,
                  })
                }
                placeholder="5000"
                required
              />

              <FormSelect
                label="Expense type"
                value={expenseForm.expense_type}
                onChange={(value) =>
                  setExpenseForm({
                    ...expenseForm,
                    expense_type: value,
                  })
                }
                options={[
                  ["item", "Item"],
                  ["event", "Event"],
                ]}
              />

              <FormSelect
                label="Spent by"
                value={expenseForm.spent_by}
                onChange={(value) =>
                  setExpenseForm({
                    ...expenseForm,
                    spent_by: value,
                  })
                }
                options={members.map((member) => [
                  member.user_id,
                  member.full_name,
                ])}
              />

              <FormSelect
                label="Payment method"
                value={expenseForm.payment_method}
                onChange={(value) =>
                  setExpenseForm({
                    ...expenseForm,
                    payment_method: value,
                  })
                }
                options={[
                  ["cash", "Cash"],
                  ["upi", "UPI"],
                  ["bank_transfer", "Bank Transfer"],
                  ["cheque", "Cheque"],
                  ["other", "Other"],
                ]}
              />

              <FormInput
                label="Date"
                type="date"
                value={expenseForm.expense_date}
                onChange={(value) =>
                  setExpenseForm({
                    ...expenseForm,
                    expense_date: value,
                  })
                }
                required
              />

              <FormInput
                label="Time"
                type="time"
                value={expenseForm.expense_time}
                onChange={(value) =>
                  setExpenseForm({
                    ...expenseForm,
                    expense_time: value,
                  })
                }
                required
              />
            </div>

            <div className="form-field">
              <label>Transaction proof</label>

              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(e) =>
                  setExpenseForm({
                    ...expenseForm,
                    proof_file: e.target.files?.[0] || null,
                  })
                }
                required
              />

              {expenseForm.proof_file && (
                <div className="proof-preview">
                  <img
                    src={URL.createObjectURL(expenseForm.proof_file)}
                    alt="Transaction proof preview"
                  />

                  <div className="proof-preview-info">
                    <strong>{expenseForm.proof_file.name}</strong>

                    <span>
                      {(expenseForm.proof_file.size / 1024 / 1024).toFixed(2)}{" "}
                      MB
                    </span>
                  </div>
                </div>
              )}
            </div>

            {expenseForm.payment_method === "cash" && (
              <div className="cash-section">
                <div className="cash-title">
                  <Wallet size={17} />
                  Cash payment details
                </div>

                <div className="form-grid">
                  <FormInput
                    label="Given to"
                    value={expenseForm.cash_details.given_to}
                    onChange={(value) =>
                      setExpenseForm({
                        ...expenseForm,
                        cash_details: {
                          ...expenseForm.cash_details,
                          given_to: value,
                        },
                      })
                    }
                    required
                  />

                  <FormInput
                    label="Location"
                    value={expenseForm.cash_details.location}
                    onChange={(value) =>
                      setExpenseForm({
                        ...expenseForm,
                        cash_details: {
                          ...expenseForm.cash_details,
                          location: value,
                        },
                      })
                    }
                    required
                  />

                  <FormInput
                    label="Purpose"
                    value={expenseForm.cash_details.purpose}
                    onChange={(value) =>
                      setExpenseForm({
                        ...expenseForm,
                        cash_details: {
                          ...expenseForm.cash_details,
                          purpose: value,
                        },
                      })
                    }
                    required
                  />
                </div>

                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={expenseForm.cash_details.organiser_known}
                    onChange={(e) =>
                      setExpenseForm({
                        ...expenseForm,
                        cash_details: {
                          ...expenseForm.cash_details,
                          organiser_known: e.target.checked,
                        },
                      })
                    }
                  />
                  Organiser knows about this
                </label>
              </div>
            )}

            <FormTextarea
              label="Notes"
              value={expenseForm.notes}
              onChange={(value) =>
                setExpenseForm({
                  ...expenseForm,
                  notes: value,
                })
              }
            />

            <button className="primary-button">Save expense</button>
          </form>
        </Modal>
      )}

      {modal === "event" && (
        <Modal title="Create event" onClose={() => setModal(null)}>
          <form className="modal-form" onSubmit={submitEvent}>
            <FormInput
              label="Event name"
              value={eventForm.event_name}
              onChange={(value) =>
                setEventForm({
                  ...eventForm,
                  event_name: value,
                })
              }
              placeholder="Cultural Program"
              required
            />

            <FormInput
              label="Planned budget"
              type="number"
              value={eventForm.planned_budget}
              onChange={(value) =>
                setEventForm({
                  ...eventForm,
                  planned_budget: value,
                })
              }
              placeholder="50000"
              required
            />

            <FormTextarea
              label="Description"
              value={eventForm.description}
              onChange={(value) =>
                setEventForm({
                  ...eventForm,
                  description: value,
                })
              }
            />

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={eventForm.budget_arranged}
                onChange={(e) =>
                  setEventForm({
                    ...eventForm,
                    budget_arranged: e.target.checked,
                  })
                }
              />
              Budget already arranged
            </label>

            <button className="primary-button">Create event</button>
          </form>
        </Modal>
      )}
    </div>
  );
}

function FormInput({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  required = false,
}) {
  return (
    <div className="form-field">
      <label>{label}</label>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        required={required}
      />
    </div>
  );
}

function FormSelect({ label, value, onChange, options }) {
  return (
    <div className="form-field">
      <label>{label}</label>

      <div className="select-wrap">
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          {options.map(([optionValue, text]) => (
            <option key={optionValue} value={optionValue}>
              {text}
            </option>
          ))}
        </select>

        <ChevronDown size={16} />
      </div>
    </div>
  );
}

function FormTextarea({ label, value, onChange }) {
  return (
    <div className="form-field">
      <label>{label}</label>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows="3"
      />
    </div>
  );
}

function RecentTransactions({ transactions, members, onViewAll }) {
  const recent = transactions.slice(0, 5);

  const getMemberName = (id) =>
    members.find((member) => member.user_id === id)?.full_name || "Unknown";

  return (
    <section className="panel transactions-panel">
      <div className="panel-header">
        <div>
          <h3>Recent transactions</h3>
          <p>Latest activity in your pandal</p>
        </div>

        <button className="text-button" onClick={onViewAll}>
          View all
        </button>
      </div>

      <TransactionTable transactions={recent} getMemberName={getMemberName} />
    </section>
  );
}

function Transactions({ transactions, members }) {
  const [searchTerm, setSearchTerm] = useState("");

  const getMemberName = (id) =>
    members.find((member) => member.user_id === id)?.full_name || "Unknown";

  const filteredTransactions = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    if (!query) {
      return transactions;
    }

    return transactions.filter((transaction) => {
      const memberName = getMemberName(transaction.user_id);

      const searchableText = [
        transaction.description,
        transaction.category,
        transaction.payment_method,
        transaction.date,
        transaction.transaction_type,
        memberName,
        transaction.amount,
      ]
        .filter((value) => value !== null && value !== undefined)
        .join(" ")
        .toLowerCase();

      return searchableText.includes(query);
    });
  }, [transactions, members, searchTerm]);

  return (
    <section className="panel transactions-panel">
      <div className="panel-header transactions-header">
        <div>
          <h3>All transactions</h3>
          <p>
            Search by transaction, category, payment method, member or date.
          </p>
        </div>

        <span className="count-badge">
          {filteredTransactions.length} of {transactions.length} records
        </span>
      </div>

      <div className="transaction-search">
        <Search size={17} />
        <input
          type="search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search transactions..."
          aria-label="Search transactions"
        />
        {searchTerm && (
          <button
            type="button"
            className="search-clear"
            onClick={() => setSearchTerm("")}
            title="Clear search"
          >
            <X size={15} />
          </button>
        )}
      </div>

      {filteredTransactions.length ? (
        <TransactionTable
          transactions={filteredTransactions}
          getMemberName={getMemberName}
        />
      ) : (
        <div className="empty-state">
          <Search size={34} />
          <h3>No matching transactions</h3>
          <p>Try a different name, category, payment method or date.</p>
        </div>
      )}
    </section>
  );
}

function TransactionTable({ transactions, getMemberName }) {
  if (!transactions.length) {
    return (
      <div className="empty-state">
        <Receipt size={34} />
        <h3>No transactions yet</h3>
        <p>Income and expenses will appear here.</p>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Transaction</th>
            <th>Date</th>
            <th>Payment</th>
            <th>Created by</th>
            <th>Amount</th>
          </tr>
        </thead>

        <tbody>
          {transactions.map((transaction) => (
            <tr key={`${transaction.transaction_type}-${transaction.id}`}>
              <td>
                <div className="transaction-name">
                  <div
                    className={
                      transaction.transaction_type === "income"
                        ? "transaction-icon income"
                        : "transaction-icon expense"
                    }
                  >
                    {transaction.transaction_type === "income" ? (
                      <ArrowDownLeft size={16} />
                    ) : (
                      <ArrowUpRight size={16} />
                    )}
                  </div>

                  <div>
                    <strong>{transaction.description}</strong>

                    <span>{transaction.category}</span>
                  </div>
                </div>
              </td>

              <td>{transaction.date}</td>

              <td>
                <span className="payment-pill">
                  {transaction.payment_method}
                </span>
              </td>

              <td>{getMemberName(transaction.user_id)}</td>

              <td
                className={
                  transaction.transaction_type === "income"
                    ? "amount-positive"
                    : "amount-negative"
                }
              >
                {transaction.transaction_type === "income" ? "+" : "-"}
                {formatMoney(transaction.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Members({ members }) {
  return (
    <section className="panel members-panel">
      <div className="panel-header">
        <div>
          <h3>Committee members</h3>
          <p>Everyone with access to this pandal</p>
        </div>

        <span className="count-badge">{members.length} members</span>
      </div>

      <div className="members-grid">
        {members.map((member) => (
          <motion.div
            className="member-card"
            key={member.user_id}
            whileHover={{ y: -3 }}
          >
            <div className="member-avatar">
              {member.full_name?.charAt(0).toUpperCase()}
            </div>

            <div>
              <strong>{member.full_name}</strong>

              <span>{member.email}</span>

              <small>
                {member.role === "admin"
                  ? "Organiser"
                  : member.role === "cashier"
                    ? "Cashier"
                    : "Viewer"}
              </small>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function InviteMembers({ pandal }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("viewer");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const sendInvitation = async (e) => {
    e.preventDefault();

    if (!pandal?.id) {
      setError("Pandal information is not available.");
      return;
    }

    setLoading(true);
    setMessage("");
    setError("");

    try {
      await api.post(`/pandals/${pandal.id}/invitations`, {
        email: email.trim().toLowerCase(),
        role,
      });

      setMessage(`Invitation created for ${email.trim().toLowerCase()}`);

      setEmail("");
      setRole("viewer");
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to create invitation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel events-panel">
      <div className="panel-header">
        <div>
          <h3>Invite Committee Members</h3>
          <p>Give trusted committee members access to this pandal.</p>
        </div>

        <div className="stat-icon">
          <UserPlus size={20} />
        </div>
      </div>

      <form className="modal-form" onSubmit={sendInvitation}>
        <div className="form-grid">
          <FormInput
            label="Gmail / Email address"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="member@gmail.com"
            required
          />

          <FormSelect
            label="Role"
            value={role}
            onChange={setRole}
            options={[
              ["viewer", "Viewer"],
              ["cashier", "Cashier"],
            ]}
          />
        </div>

        <div className="invite-role-info">
          {role === "viewer" ? (
            <>
              <strong>Viewer access</strong>
              <span>
                Can view the dashboard, transactions and committee information.
                Cannot add or edit financial records.
              </span>
            </>
          ) : (
            <>
              <strong>Cashier access</strong>
              <span>
                Can view the dashboard and add income, expenses and transaction
                proofs.
              </span>
            </>
          )}
        </div>

        {message && <div className="success-message">{message}</div>}

        {error && <div className="error-message">{error}</div>}

        <button className="primary-button" type="submit" disabled={loading}>
          <UserPlus size={17} />
          {loading ? "Creating invitation..." : "Send Invitation"}
        </button>
      </form>

      <div className="invite-note">
        <ShieldCheck size={17} />
        <div>
          <strong>How it works</strong>
          <p>
            The invitation is linked to the email address. When the invited
            person registers with the same email, they can automatically join
            this pandal.
          </p>
        </div>
      </div>
    </section>
  );
}

function Events({ events, isOrganiser, onAdd }) {
  return (
    <section className="panel events-panel">
      <div className="panel-header">
        <div>
          <h3>Planned Events</h3>
          <p>
            Track planned events, budgets and whether the amount is arranged.
          </p>
        </div>

        {isOrganiser && (
          <button className="quick-income" onClick={onAdd}>
            <Plus size={17} />
            Create Event
          </button>
        )}
      </div>

      {!events.length ? (
        <div className="empty-state">
          <CalendarDays size={38} />
          <h3>No events planned yet</h3>
          <p>Create an event to start tracking its planned budget.</p>
        </div>
      ) : (
        <div className="event-list">
          {events.map((event) => (
            <motion.div
              className="event-card"
              key={event.id}
              whileHover={{ y: -3 }}
            >
              <div className="event-card-main">
                <div className="event-icon">
                  <CalendarDays size={20} />
                </div>

                <div className="event-info">
                  <h3>{event.event_name}</h3>
                  {event.description && <p>{event.description}</p>}
                </div>
              </div>

              <div className="event-budget">
                <span>Planned budget</span>
                <strong>{formatMoney(event.planned_budget)}</strong>
              </div>

              <div
                className={
                  event.budget_arranged
                    ? "event-status arranged"
                    : "event-status pending"
                }
              >
                <span className="event-status-dot" />
                {event.budget_arranged
                  ? "Amount arranged"
                  : "Amount not arranged"}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </section>
  );
}

export default Dashboard;
