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

	const [data_received, setdata_received] = useState();

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
			console.log("Dates:", dates);
			const [startDate, endDate] = dates;
			axios
				.post(
					"/dashboard_names?startDate=" +
						moment(startDate).format("YYYY-MM-DD") +
						"&endDate=" +
						moment(endDate).format("YYYY-MM-DD") +
						"&blocks=" +
						blocks +
						"&error_percent=" +
						error_percent,
					{}
				)
				.then((response) => {
					// Handle the response from the server

					if (response.data) {
						const documentStyle = getComputedStyle(document.documentElement);
						const data = {
							labels: [
								"No. of Tie-Lines with Error",
								"No. of Tie-Lines without Error",
							],
							datasets: [
								{
									data: [
										response.data.total_count[0],
										response.data.total_count[1] - response.data.total_count[0],
									],
									backgroundColor: [
										documentStyle.getPropertyValue("--red-500"),
										documentStyle.getPropertyValue("--green-500"),
										// documentStyle.getPropertyValue("--green-500"),
									],
									hoverBackgroundColor: [
										documentStyle.getPropertyValue("--red-400"),
										documentStyle.getPropertyValue("--green-400"),
										// documentStyle.getPropertyValue("--green-400"),
									],
								},
							],
						};
						const options = {
							plugins: {
								legend: {
									labels: {
										usePointStyle: true,
									},
								},
							},
						};
						setChartData(data);
						setChartOptions(options);
					}

					const summary = Object.fromEntries(
						Object.entries(response.data)
							.filter(([k]) => k !== "total_count")
							.map(([k, v]) => [
								k,
								[
									v.length,
									v.filter((i) => i[1] === 0).length,
									v.filter((i) => i[1] === 1).length,
								],
							])
					);

					const documentStyle = getComputedStyle(document.documentElement);
					const textColor = documentStyle.getPropertyValue("--text-color");
					const textColorSecondary = documentStyle.getPropertyValue(
						"--text-color-secondary"
					);
					const surfaceBorder =
						documentStyle.getPropertyValue("--surface-border");

					// response.data.BH 85
					// response.data.DV 32
					// response.data.GR 52
					// response.data.JH 35
					// response.data.MIS_CALC_TO 41
					// response.data.NTPC_ER_1 2
					// response.data.NTPC_ODISHA 0
					// response.data.PG_ER1 144
					// response.data.PG_ER2 76
					// response.data.PG_odisha_project 64
					// response.data.SI 4
					// response.data.WB 52

					const data1 = {
						labels: [
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
						],
						datasets: [
							{
								type: "line",
								label: "% of Tie-Lines with Error",
								borderColor: documentStyle.getPropertyValue("--blue-500"),
								borderWidth: 2,
								fill: false,
								tension: 0.4,
								data: [
									((summary.BH[0] / 85) * 100).toFixed(2),
									((summary.DV[0] / 32) * 100).toFixed(2),
									((summary.GR[0] / 52) * 100).toFixed(2),
									((summary.JH[0] / 35) * 100).toFixed(2),
									((summary.SI[0] / 4) * 100).toFixed(2),
									((summary.WB[0] / 52) * 100).toFixed(2),
									((summary.NTPC_ER_1[0] / 2) * 100).toFixed(2),
									0,
									((summary.PG_ER1[0] / 144) * 100).toFixed(2),
									((summary.PG_ER2[0] / 76) * 100).toFixed(2),
									((summary.PG_odisha_project[0] / 64) * 100).toFixed(2),
									((summary.MIS_CALC_TO[0] / 41) * 100).toFixed(2),
								],
								yAxisID: "y1",
							},
							{
								type: "bar",
								label: "To-End Tie-Lines with Error",
								backgroundColor: documentStyle.getPropertyValue("--green-500"),
								data: [
									summary.BH[1],
									summary.DV[1],
									summary.GR[1],
									summary.JH[1],
									summary.SI[1],
									summary.WB[1],
									summary.NTPC_ER_1[1],
									summary.NTPC_ODISHA[1],
									summary.PG_ER1[1],
									summary.PG_ER2[1],
									summary.PG_odisha_project[1],
									summary.MIS_CALC_TO[1],
								],
								borderColor: "white",
								borderWidth: 2,
							},
							{
								type: "bar",
								label: "Far End Tie-Lines with Error",
								backgroundColor: documentStyle.getPropertyValue("--red-500"),
								data: [
									summary.BH[2],
									summary.DV[2],
									summary.GR[2],
									summary.JH[2],
									summary.SI[2],
									summary.WB[2],
									summary.NTPC_ER_1[2],
									summary.NTPC_ODISHA[2],
									summary.PG_ER1[2],
									summary.PG_ER2[2],
									summary.PG_odisha_project[2],
									summary.MIS_CALC_TO[2],
								],
							},
						],
					};
					const options1 = {
						maintainAspectRatio: false,
						aspectRatio: 0.6,
						plugins: {
							legend: {
								labels: {
									color: textColor,
								},
							},
						},

						scales: {
							x: {
								title: {
									display: true,
									text: "Constituents",
								},
								ticks: {
									color: textColorSecondary,
								},
								grid: {
									color: surfaceBorder,
								},
							},
							y: {
								title: {
									display: true,
									text: "No. of Tie-Lines with Error ",
								},
								type: "linear",
								display: true,
								position: "left",
								ticks: {
									color: textColorSecondary,
								},
								grid: {
									color: surfaceBorder,
								},
							},
							y1: {
								title: {
									display: true,
									text: "% of Tie-Lines with Error ",
								},
								type: "linear",
								display: true,
								position: "right",
								ticks: {
									color: textColorSecondary,
								},
								grid: {
									drawOnChartArea: true,
									color: surfaceBorder,
								},
							},
						},
					};

					setChartData1(data1);
					setChartOptions1(options1);
				})
				.catch((error) => {
					// Handle any errors
					console.error(error);
				});
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
								padding: 1.5rem 1rem;
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
				<div className="charts-section">
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
									style={{ width: "32vh", height: "32vh" }}
									className="w-auto"
								/>
								<div className="chart-label">
									Number of Tie-Lines with Error (Pie-Chart)
								</div>
							</div>
							{/* <div className="chart-container">
								<Chart
									type="doughnut"
									data={chartData}
									options={chartOptions}
									style={{ width: "32vh", height: "32vh" }}
									className="w-auto"
								/>
								<div className="chart-label">
									Error Distribution by Category
								</div>
							</div> */}
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
					</div>
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
