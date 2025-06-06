import React, { useEffect, useState } from "react";
import axios from "axios";
// import { Column } from "primereact/column";
// import { DataTable } from "primereact/datatable";
import moment from "moment";
import { jwtDecode } from "jwt-decode";
import { useLocation } from "react-router-dom";
import { Fieldset } from "primereact/fieldset";
import { Avatar } from "primereact/avatar";
import { Divider } from "primereact/divider";
import { Button } from "primereact/button";
import { BlockUI } from "primereact/blockui";
import { Chart } from "primereact/chart";
import { Calendar } from "primereact/calendar";
import { InputNumber } from "primereact/inputnumber";

function Dashboard(params) {
	const search = useLocation().search;
	const id = new URLSearchParams(search).get("token");
	const [page_hide, setpage_hide] = useState(true);
	params.var1(page_hide);
	const [meter_date, setmeter_date] = useState();
	const [scada_db_date, setscada_db_date] = useState();
	const [meter_folder_date, setmeter_folder_date] = useState();
	const [User_id, setUser_id] = useState();
	const [Person_Name, setPerson_Name] = useState();
	const [Department, setDepartment] = useState();
	// const [isAdmin, setisAdmin] = useState(false);
	const [blocked, setBlocked] = useState(false);
	const [loading_show, setloading_show] = useState(false);

	const [chartData, setChartData] = useState({});
	const [chartOptions, setChartOptions] = useState({});
	const [dates, setDates] = useState(null);
	const [error_percent, seterror_percent] = useState(3);
	const [blocks, setblocks] = useState(70);

	const [chartData1, setChartData1] = useState({});
	const [chartOptions1, setChartOptions1] = useState({});

	useEffect(() => {
		if (!id) {
			setpage_hide(false);
			params.var2("Invalid_Token");
			return;
		}

		const fetchDashboardData = async () => {
			try {
				const { data } = await axios.post("/dashboard");
				if (data) {
					const meterDateRaw = data[0]?.meter_date?.[0]?.date;
					const scadaDateRaw = data[0]?.scada_db_date?.[0]?.Date;
					setmeter_date({
						date: meterDateRaw
							? moment(meterDateRaw).format("DD-MM-YYYY")
							: "-",
					});
					setscada_db_date({
						Date: scadaDateRaw
							? moment(scadaDateRaw).format("DD-MM-YYYY")
							: "-",
					});
					setmeter_folder_date(data[0]?.meter_folder_date || []);
					const meterDate = meterDateRaw ? new Date(meterDateRaw) : null;
					const scadaDate = scadaDateRaw ? new Date(scadaDateRaw) : null;
					if (meterDate && scadaDate) {
						const minDate = meterDate < scadaDate ? meterDate : scadaDate;
						const sixDaysAgo = new Date(minDate);
						sixDaysAgo.setDate(minDate.getDate() - 6);
						setDates([sixDaysAgo, minDate]);
					}
				}
			} catch {}
		};

		const verifyToken = async () => {
			try {
				const { data } = await axios.get("https://sso.erldc.in:5000/verify", {
					headers: { Token: id },
				});
				if (data === "User has logout" || data === "Bad Token") {
					alert(
						data === "User has logout"
							? "User Logged-out, Please login via SSO again"
							: "Unauthorised Access, Please login via SSO again"
					);
					window.location = "https://sso.erldc.in:3000";
					setpage_hide(true);
					return;
				}
				const decoded = jwtDecode(data["Final_Token"], "it@posoco");
				if (!decoded["Login"] && decoded["Reason"] === "Session Expired") {
					alert("Session Expired, Please Login Again via SSO");
					try {
						await axios.post("https://sso.erldc.in:5000/1ogout", {
							headers: { token: id },
						});
					} catch {}
					window.location = "https://sso.erldc.in:3000";
					return;
				}
				setUser_id(decoded["User"]);
				setpage_hide(!decoded["Login"]);
				setPerson_Name(decoded["Person_Name"]);
				const dept = decoded["Department"];
				const deptMap = {
					"IT-TS": "Information Technology (IT)",
					IT: "Information Technology (IT)",
					MO: "Market Operation (MO)",
					"MO-I": "Market Operation (MO)",
					"MO-II": "Market Operation (MO)",
					"MO-III": "Market Operation (MO)",
					"MO-IV": "Market Operation (MO)",
					MIS: "System Operation (SO)",
					SS: "System Operation (SO)",
					CR: "Control Room (CR)",
					SO: "System Operation (SO)",
					SCADA: "SCADA",
					CS: "Contracts & Services (CS)",
					TS: "Technical Services (TS)",
					HR: "Human Resource (HR)",
					COMMUNICATION: "Communication",
					"F&A": "Finance & Accounts (F&A)",
				};
				setDepartment(deptMap[dept] || dept);
			} catch {}
		};

		params.var2(id);

		fetchDashboardData();
		verifyToken();
	}, [id]);

	useEffect(() => {
		if (dates && dates.length === 2 && dates[0] !== null && dates[1] !== null) {
			const [startDate, endDate] = dates;
			(async () => {
				try {
					const { data } = await axios.post(
						`/dashboard_names?startDate=${moment(startDate).format(
							"YYYY-MM-DD"
						)}&endDate=${moment(endDate).format(
							"YYYY-MM-DD"
						)}&blocks=${blocks}&error_percent=${error_percent}`,
						{}
					);

					if (!data) return;

					const documentStyle = getComputedStyle(document.documentElement);

					// Pie/Doughnut Chart Data
					setChartData({
						labels: [
							"No. of Tie-Lines with Error",
							"No. of Tie-Lines without Error",
						],
						datasets: [
							{
								data: [
									data.total_count[0],
									data.total_count[1] - data.total_count[0],
								],
								backgroundColor: [
									documentStyle.getPropertyValue("--pink-500"),
									documentStyle.getPropertyValue("--blue-500"),
								],
								hoverBackgroundColor: [
									documentStyle.getPropertyValue("--pink-400"),
									documentStyle.getPropertyValue("--blue-400"),
								],
							},
						],
					});
					setChartOptions({
						plugins: {
							legend: { labels: { usePointStyle: true } },
						},
					});

					// Prepare summary and name_object
					const summary = {};
					const name_object = {};
					for (const [k, v] of Object.entries(data)) {
						if (k === "total_count") continue;
						summary[k] = [
							v.length,
							v.filter((i) => i[1] === 0).length,
							v.filter((i) => i[1] === 1).length,
						];
						const map = {};
						for (const [name, val] of v) {
							map[name] = map[name] || new Set();
							map[name].add(val);
						}
						name_object[k] = Object.entries(map).map(([name, set]) => {
							const has0 = set.has(0),
								has1 = set.has(1);
							return `${name} ${
								has0 && has1 ? "Both End" : has0 ? "To End" : "Far End"
							}`;
						});
					}

					// Chart labels and keys
					const chartLabels = [
						"BIHAR",
						"DVC",
						"ODISHA",
						"JHARKHAND",
						"SIKKIM",
						"WEST-BENGAL",
						"NTPC ER1",
						"NTPC ODISHA",
						"PG ER1",
						"PG ER2",
						"PG ODISHA PROJECT",
						"MIS CALC TO",
					];
					const chartKeys = [
						"BH",
						"DV",
						"GR",
						"JH",
						"SI",
						"WB",
						"NTPC_ER_1",
						"NTPC_ODISHA",
						"PG_ER1",
						"PG_ER2",
						"PG_odisha_project",
						"MIS_CALC_TO",
					];
					const chartDivisors = [85, 32, 52, 35, 4, 52, 2, 0, 144, 76, 64, 41];

					// Line/Bar Chart Data
					setChartData1({
						labels: chartLabels,
						datasets: [
							{
								type: "line",
								label: "% of Tie-Lines with Error",
								borderColor: documentStyle.getPropertyValue("--green-500"),
								borderWidth: 2,
								fill: false,
								tension: 0.4,
								data: chartKeys.map((k, i) =>
									chartDivisors[i]
										? (
												((summary[k]?.[0] || 0) / chartDivisors[i]) *
												100
										  ).toFixed(2)
										: 0
								),
								yAxisID: "y1",
							},
							{
								type: "bar",
								label: "To-End Tie-Lines with Error",
								backgroundColor: documentStyle.getPropertyValue("--pink-500"),
								data: chartKeys.map((k) => summary[k]?.[1] || 0),
								borderColor: "white",
								borderWidth: 2,
							},
							{
								type: "bar",
								label: "Far End Tie-Lines with Error",
								backgroundColor: documentStyle.getPropertyValue("--blue-500"),
								data: chartKeys.map((k) => summary[k]?.[2] || 0),
							},
						],
					});

					const textColor = documentStyle.getPropertyValue("--text-color");
					const textColorSecondary = documentStyle.getPropertyValue(
						"--text-color-secondary"
					);
					const surfaceBorder =
						documentStyle.getPropertyValue("--surface-border");

					setChartOptions1({
						maintainAspectRatio: false,
						aspectRatio: 0.6,
						plugins: {
							legend: { labels: { color: textColor } },
							tooltip: {
								enabled: true,
								mode: "nearest",
								intersect: false,
								callbacks: {
									label: (context) => {
										const idx = chartLabels.indexOf(context.label);
										const key = chartKeys[idx];
										const display = chartLabels[idx];
										const names = name_object[key] || [];
										return [`${display}: ${context.parsed.y}`, ...names];
									},
								},
							},
						},
						hover: { mode: "nearest", intersect: true },
						scales: {
							x: {
								title: { display: true, text: "Constituents" },
								ticks: { color: textColorSecondary },
								grid: { color: surfaceBorder },
							},
							y: {
								title: { display: true, text: "No. of Tie-Lines with Error " },
								type: "linear",
								display: true,
								position: "left",
								ticks: { color: textColorSecondary },
								grid: { color: surfaceBorder },
							},
							y1: {
								title: { display: true, text: "% of Tie-Lines with Error " },
								type: "linear",
								display: true,
								position: "right",
								ticks: { color: textColorSecondary },
								grid: { drawOnChartArea: true, color: surfaceBorder },
							},
						},
					});
				} catch (error) {
					console.error(error);
				}
			})();
		}
	}, [dates, blocks, error_percent]);

	const folder_delete = () => {
		axios
			.post("/folder_delete")
			.then((response) => {
				alert(response.data);
				setBlocked(false);
				setloading_show(false);
			})
			.catch((error) => {});
	};

	return (
		<>
			{/* Loader Overlay */}
			{loading_show && (
				<div className="loader-overlay">
					<div className="loader">
						<div className="spinner"></div>
					</div>
				</div>
			)}
			<BlockUI blocked={blocked} fullScreen />

			{/* Login Prompt */}
			{page_hide && (
				<Fieldset>
					<div className="centered-content">
						<h1>Please Login again by SSO</h1>
					</div>
				</Fieldset>
			)}

			<br />
			{/* Welcome Banner */}
			{!page_hide && (
				<div className="welcome-banner">
					<span className="scrolling-text">
						Welcome&nbsp;
						<b>
							Sh. {Person_Name} ({User_id})
						</b>
						&nbsp;of&nbsp;<b>{Department}</b>
					</span>
					<style>
						{`
							.welcome-banner {
								width: 100%;
								overflow: hidden;
								background: #f4f4f4;
								padding: 0.5rem 0;
								border-radius: 8px;
								margin-bottom: 1rem;
								box-shadow: 0 2px 8px rgba(0,0,0,0.04);
							}
							.scrolling-text {
								display: inline-block;
								padding-left: 100%;
								white-space: nowrap;
								animation: scroll-left 18s linear infinite;
								font-size: 1.1rem;
								color: #222;
							}
							@keyframes scroll-left {
								0% { transform: translateX(0); }
								100% { transform: translateX(-100%); }
							}
							.centered-content {
								display: flex;
								justify-content: center;
								align-items: center;
								min-height: 120px;
							}
							.loader-overlay {
								position: fixed;
								top: 0; left: 0; right: 0; bottom: 0;
								background: rgba(255,255,255,0.7);
								z-index: 9999;
								display: flex;
								align-items: center;
								justify-content: center;
							}
						`}
					</style>
				</div>
			)}

			{/* Dashboard Info */}
			<Divider align="left" hidden={!page_hide}>
				<span
					className="p-tag"
					style={{ backgroundColor: "#000", fontSize: "large" }}
				>
					<Avatar
						icon="pi pi-sitemap"
						style={{ backgroundColor: "#000", color: "#fff" }}
						shape="square"
					/>
					Dashboard
				</span>
			</Divider>

			{!page_hide && (
				<div className="dashboard-info-row">
					<div className="dashboard-info-item">
						<strong>Scada DB Up-To:</strong>
						<div>{scada_db_date?.Date || "-"}</div>
					</div>
					<div className="dashboard-info-item">
						<strong>Meter DB Up-To:</strong>
						<div>{meter_date?.date || "-"}</div>
					</div>
					<div className="dashboard-info-item">
						<strong>Meter Folder Up-To:</strong>
						<div>
							{meter_folder_date && meter_folder_date.length > 0
								? meter_folder_date[0].meter_folder_date
								: "-"}
						</div>
					</div>
					<div className="dashboard-info-item">
						<Button
							size="small"
							rounded
							raised
							severity="danger"
							label="Delete Folder Files"
							icon="pi pi-delete-left"
							onClick={() => {
								folder_delete();
								setloading_show(true);
								setBlocked(true);
							}}
						/>
					</div>
					<style>
						{`
							.dashboard-info-row {
								display: flex;
								flex-wrap: wrap;
								justify-content: space-between;
								align-items: center;
								gap: 1.5rem;
								margin-bottom: 2rem;
								background: #fff;
								padding-left: 1.5rem;
								padding-right: 1rem;
								border-radius: 8px;
								box-shadow: 0 2px 8px rgba(0,0,0,0.04);
							}
							.dashboard-info-item {
								min-width: 180px;
								margin-bottom: 0.5rem;
								font-size: 1rem;
							}
						`}
					</style>
				</div>
			)}

			{/* Charts Section */}
			<Divider align="center" hidden={!page_hide}>
				<span
					className="p-tag"
					style={{ backgroundColor: "#000", fontSize: "large" }}
				>
					<Avatar
						icon="pi pi-chart-pie"
						style={{ backgroundColor: "#000", color: "#fff" }}
						shape="square"
					/>
					Charts
				</span>
			</Divider>

			{!page_hide && (
				<div className="charts-section" style={{ marginTop: "-3rem" }}>
					<div className="charts-row">
						<div className="charts-controls">
							<div className="charts-control">
								<label htmlFor="percent" className="font-bold block mb-2">
									Error Percent:
								</label>
								<InputNumber
									showButtons
									step={1}
									size={2}
									inputId="percent"
									value={error_percent}
									onValueChange={(e) => seterror_percent(e.value)}
									suffix=" %"
									max={100}
									min={0}
								/>
							</div>
							<div className="charts-control">
								<label htmlFor="blocks" className="font-bold block mb-2">
									Number of Blocks:
								</label>
								<InputNumber
									showButtons
									step={1}
									size={5}
									inputId="blocks"
									value={blocks}
									onValueChange={(e) => setblocks(e.value)}
									suffix=" Blocks"
									min={0}
									max={1000}
								/>
							</div>
							<div className="charts-control">
								<label htmlFor="daterange" className="font-bold block mb-2">
									Date Range:
								</label>
								<Calendar
									showIcon
									value={dates}
									onChange={(e) => setDates(e.value)}
									selectionMode="range"
									readOnlyInput
									hideOnRangeSelection
									dateFormat="dd-mm-yy"
									placeholder="Select Date Range"
									inputId="daterange"
								/>
							</div>
						</div>
						<div className="charts-visuals">
							<div className="chart-container">
								<Chart
									type="pie"
									data={chartData}
									options={chartOptions}
									style={{ width: "40vh", height: "35vh" }}
									className="w-auto"
								/>
								<div className="chart-label">
									Number of Tie-Lines with Error (Pie-Chart) <br /> Total
									Tie-Lines:373
								</div>
							</div>

							<div className="chart-container">
								<Chart
									type="line"
									data={chartData1}
									options={chartOptions1}
									style={{ width: "100vh", height: "40vh" }}
								/>
								<div className="chart-label">
									Tie-Lines Error Analysis (Bar & Line Chart)
								</div>
							</div>
						</div>
					</div>

					<Divider align="left" hidden={!page_hide}>
						{/* <span
							className="p-tag"
							style={{ backgroundColor: "#000", fontSize: "large" }}
						>
							<Avatar
								icon="pi pi-chart-pie"
								style={{ backgroundColor: "#000", color: "#fff" }}
								shape="square"
							/>
							Charts
						</span> */}
					</Divider>
					{/* Repeated Charts Section */}
					{/* <div className="charts-row">
						<div className="charts-controls">
							<div className="charts-control">
								<label htmlFor="percent" className="font-bold block mb-2">
									Error Percent:
								</label>
								<InputNumber
									showButtons
									step={1}
									size={2}
									inputId="percent"
									value={error_percent}
									onValueChange={(e) => seterror_percent(e.value)}
									suffix=" %"
									max={100}
									min={0}
								/>
							</div>
							<div className="charts-control">
								<label htmlFor="blocks" className="font-bold block mb-2">
									Number of Blocks:
								</label>
								<InputNumber
									showButtons
									step={1}
									size={5}
									inputId="blocks"
									value={blocks}
									onValueChange={(e) => setblocks(e.value)}
									suffix=" Blocks"
									min={0}
									max={1000}
								/>
							</div>
							<div className="charts-control">
								<label htmlFor="daterange" className="font-bold block mb-2">
									Date Range:
								</label>
								<Calendar
									showIcon
									value={dates}
									onChange={(e) => setDates(e.value)}
									selectionMode="range"
									readOnlyInput
									hideOnRangeSelection
									dateFormat="dd-mm-yy"
									placeholder="Select Date Range"
									inputId="daterange"
								/>
							</div>
						</div>
						<div className="charts-visuals">
							<div className="chart-container">
								<Chart
									type="doughnut"
									data={chartData}
									options={chartOptions}
									style={{ width: "32vh", height: "32vh" }}
									className="w-auto"
								/>
								<div className="chart-label">
									Number of Tie-Lines with Error (Pie-Chart) <br /> Total
									Tie-Lines:373
								</div>
							</div>

							<div className="chart-container">
								<Chart
									type="line"
									data={chartData1}
									options={chartOptions1}
									style={{ width: "100vh", height: "32vh" }}
								/>
								<div className="chart-label">
									Tie-Lines Error Analysis (Bar & Line Chart)
								</div>
							</div>
						</div>
					</div> */}
					<style>
						{`
							.charts-section {
								background: #fff;
								padding: 2rem 1rem;
								border-radius: 8px;
								box-shadow: 0 2px 8px rgba(0,0,0,0.04);
								margin-bottom: 2rem;
							}
							.charts-row {
								display: flex;
								flex-direction: column;
								gap: 2rem;
							}
							@media (min-width: 900px) {
								.charts-row {
									flex-direction: row;
									align-items: flex-start;
								}
							}
							.charts-controls {
								display: flex;
								flex-direction: column;
								gap: 1.5rem;
								flex: 1 1 300px;
								max-width: 350px;
							}
							.charts-control {
								margin-bottom: 0.5rem;
							}
							.charts-visuals {
								display: flex;
								flex-direction: row;
								gap: 2rem;
								justify-content: center;
								align-items: flex-start;
								flex: 2 1 500px;
							}
							.chart-container {
								display: flex;
								flex-direction: column;
								align-items: center;
								background: #f9f9f9;
								padding: 1rem 1.5rem;
								border-radius: 8px;
								box-shadow: 0 1px 4px rgba(0,0,0,0.03);
							}
							.chart-label {
								text-align: center;
								margin-top: 0.5rem;
								font-weight: bold;
								font-size: 1rem;
								color: #333;
							}
						`}
					</style>
				</div>
			)}
		</>
	);
}
export default Dashboard;
