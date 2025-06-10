import React, { useEffect, useState } from "react";
import axios from "axios";
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
import "../cssfiles/Animation.css";
import "../cssfiles/PasswordDemo.css";
import "primeflex/primeflex.css";
import "primereact/resources/themes/lara-light-indigo/theme.css"; //theme
import "primereact/resources/primereact.min.css"; //core css
import "primeicons/primeicons.css"; //icons
import "../cssfiles/ButtonDemo.css";

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
	const [maxdate, setMaxdate] = useState(null);
	const [dates, setDates] = useState(null);
	const [error_percent, seterror_percent] = useState(3);
	const [blocks, setblocks] = useState(70);

	const [onedate, setOnedate] = useState(null);
	const [one_error, setOneError] = useState(3);

	const [chartData1, setChartData1] = useState({});
	const [chartOptions1, setChartOptions1] = useState({});

	const [chartData2, setChartData2] = useState({});
	const [chartOptions2, setChartOptions2] = useState({});

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
						setMaxdate(minDate);
						setOnedate(minDate);
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

					// Pie Chart Data (visually appealing, matching bar chart style)
					setChartData({
						labels: [
							`Tie-Lines with Error (${data.total_count[0]})`,
							`Tie-Lines without Error (${
								data.total_count[1] - data.total_count[0]
							})`,
						],
						datasets: [
							{
								data: [
									data.total_count[0],
									data.total_count[1] - data.total_count[0],
								],
								backgroundColor: [
									documentStyle.getPropertyValue("--red-300"),
									documentStyle.getPropertyValue("--green-300"),
								],
								borderColor: [
									documentStyle.getPropertyValue("--red-500"),
									documentStyle.getPropertyValue("--green-500"),
								],
								hoverBackgroundColor: [
									documentStyle.getPropertyValue("--red-200"),
									documentStyle.getPropertyValue("--green-200"),
								],
								borderWidth: 3,
								borderRadius: 12,
								hoverOffset: 16,
							},
						],
					});
					setChartOptions({
						responsive: true,
						maintainAspectRatio: false,
						plugins: {
							legend: {
								labels: {
									color: documentStyle.getPropertyValue("--text-color"),
									font: { size: 15, weight: "bold" },
									usePointStyle: true,
									padding: 20,
								},
								position: "top",
								align: "center",
							},
							title: {
								display: true,
								text: "Tie-Lines Error Pie-Chart (332 Tie-Lines)",
								color: documentStyle.getPropertyValue("--text-color"),
								font: { size: 20, weight: "bold" },
								padding: { top: 10, bottom: 30 },
							},
							tooltip: {
								enabled: true,
								backgroundColor: "#222",
								titleColor: "#fff",
								bodyColor: "#fff",
								borderColor: "#aaa",
								borderWidth: 1,
								padding: 12,
								caretSize: 8,
								displayColors: true,
								callbacks: {
									label: (context) => {
										const total = data.total_count[1];
										const value = context.parsed;
										const percent = ((value / total) * 100).toFixed(2);
										return `${context.label}: ${value} (${percent}%)`;
									},
								},
							},
							datalabels: {
								display: true,
								color: "#222",
								font: { weight: "bold", size: 13 },
								anchor: "end",
								align: "end",
								formatter: (value, ctx) => {
									const total = ctx.chart.data.datasets[0].data.reduce(
										(a, b) => a + b,
										0
									);
									return ((value / total) * 100).toFixed(1) + "%";
								},
							},
						},
						animation: {
							animateRotate: true,
							animateScale: true,
							duration: 1200,
							easing: "easeInOutQuart",
						},
						layout: {
							padding: {
								left: 10,
								right: 10,
								top: 10,
								bottom: 10,
							},
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
						name_object[k] = [
							Object.entries(map)
								.filter(([_, set]) => set.has(0))
								.map(([name, set]) => `${name} To End`),
							Object.entries(map)
								.filter(([_, set]) => set.has(1))
								.map(([name]) => `${name} Far End`),
						];
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
					];
					const chartDivisors = [85, 32, 52, 35, 4, 52, 2, 0, 144, 76, 64];

					// Line/Bar Chart Data
					setChartData1({
						labels: chartLabels,
						datasets: [
							{
								type: "line",
								label: "% of Tie-Lines with Error",
								borderColor: documentStyle.getPropertyValue("--green-500"),
								backgroundColor: "rgba(34,197,94,0.15)",
								borderWidth: 3,
								pointBackgroundColor:
									documentStyle.getPropertyValue("--green-500"),
								pointBorderColor: "#fff",
								pointRadius: 7,
								pointHoverRadius: 10,
								pointStyle: "rectRounded",
								fill: true,
								tension: 0.45,
								data: chartKeys.map((k, i) =>
									chartDivisors[i]
										? (
												((summary[k]?.[0] || 0) / chartDivisors[i]) *
												100
										  ).toFixed(2)
										: 0
								),
								yAxisID: "y1",
								order: 2,
							},
							{
								type: "bar",
								label: "To-End Tie-Lines with Error",
								backgroundColor: documentStyle.getPropertyValue("--pink-300"),
								borderColor: documentStyle.getPropertyValue("--pink-500"),
								borderWidth: 2,
								borderRadius: 8,
								barPercentage: 0.7,
								categoryPercentage: 0.6,
								data: chartKeys.map((k) => summary[k]?.[1] || 0),
								order: 1,
							},
							{
								type: "bar",
								label: "Far End Tie-Lines with Error",
								backgroundColor: documentStyle.getPropertyValue("--blue-300"),
								borderColor: documentStyle.getPropertyValue("--blue-500"),
								borderWidth: 2,
								borderRadius: 8,
								barPercentage: 0.7,
								categoryPercentage: 0.6,
								data: chartKeys.map((k) => summary[k]?.[2] || 0),
								order: 1,
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
							legend: {
								labels: {
									color: textColor,
									font: { size: 15, weight: "bold" },
									usePointStyle: true,
									padding: 20,
								},
								position: "top",
								align: "center",
								onClick: (e, legendItem, legend) => {
									const ci = legend.chart;
									const index = legendItem.datasetIndex;
									const meta = ci.getDatasetMeta(index);
									meta.hidden =
										meta.hidden === null
											? !ci.data.datasets[index].hidden
											: null;
									ci.update();
								},
							},
							title: {
								display: true,
								text: "Tie-Lines Error Analysis by Constituent",
								color: textColor,
								font: { size: 20, weight: "bold" },
								padding: { top: 10, bottom: 30 },
							},
							tooltip: {
								enabled: true,
								mode: "nearest",
								intersect: false,
								backgroundColor: "#222",
								titleColor: "#fff",
								bodyColor: "#fff",
								borderColor: "#aaa",
								borderWidth: 1,
								padding: 12,
								caretSize: 8,
								displayColors: true,
								callbacks: {
									label: (context) => {
										const idx = chartLabels.indexOf(context.label);
										const key = chartKeys[idx];
										const display = chartLabels[idx];
										// const names = name_object[key] || [];

										if (context.dataset.type === "line") {
											return [
												"% of Tie-Line with Error: " + context.parsed.y + "%",
											];
										} else {
											if (
												context.dataset.label === "To-End Tie-Lines with Error"
											) {
												const names = name_object[key][0] || [];
												return [
													`${display} To End has: ${context.parsed.y} Tie-Lines`,
													...names,
												];
											} else {
												const names = name_object[key][1] || [];
												return [
													`${display} Far End has: ${context.parsed.y} Tie-Lines`,
													...names,
												];
											}
										}
									},
								},
							},

							datalabels: {
								display: true,
								color: "#222",
								font: { weight: "bold", size: 13 },
								anchor: "end",
								align: "top",
								formatter: (value, ctx) => {
									if (ctx.dataset.type === "line") {
										return value + "%";
									}
									return value;
								},
							},
							zoom: {
								zoom: {
									wheel: { enabled: true },
									pinch: { enabled: true },
									mode: "xy",
								},
								pan: {
									enabled: true,
									mode: "xy",
								},
							},
						},
						hover: { mode: "nearest", intersect: true, animationDuration: 400 },
						animation: {
							duration: 1200,
							easing: "easeInOutQuart",
						},
						scales: {
							x: {
								title: {
									display: true,
									text: "Constituents",
									color: textColor,
									font: { size: 16, weight: "bold" },
								},
								ticks: {
									color: textColorSecondary,
									font: { size: 13, weight: "bold" },
									autoSkip: false,
									maxRotation: 30,
									minRotation: 0,
								},
								grid: {
									color: surfaceBorder,
									borderDash: [4, 4],
								},
							},
							y: {
								title: {
									display: true,
									text: "No. of Tie-Lines with Error",
									color: textColor,
									font: { size: 15, weight: "bold" },
								},
								type: "linear",
								display: true,
								position: "left",
								ticks: {
									color: textColorSecondary,
									font: { size: 13 },
									stepSize: 1,
									beginAtZero: true,
								},
								grid: {
									color: surfaceBorder,
									drawBorder: true,
									borderDash: [4, 4],
								},
							},
							y1: {
								title: {
									display: true,
									text: "% of Tie-Lines with Error",
									color: textColor,
									font: { size: 15, weight: "bold" },
								},
								type: "linear",
								display: true,
								position: "right",
								ticks: {
									color: textColorSecondary,
									font: { size: 13 },
									callback: (val) => val + "%",
									beginAtZero: true,
								},
								grid: {
									drawOnChartArea: false,
								},
							},
						},
						layout: {
							padding: {
								left: 10,
								right: 10,
								top: 10,
								bottom: 10,
							},
						},
						responsive: true,
						elements: {
							bar: {
								borderSkipped: false,
								borderRadius: 8,
							},
							point: {
								radius: 7,
								hoverRadius: 10,
								backgroundColor: documentStyle.getPropertyValue("--green-300"),
								borderColor: "#fff",
								borderWidth: 2,
							},
						},
					});
				} catch (error) {
					console.error(error);
				}
			})();
		}
	}, [dates, blocks, error_percent]);

	useEffect(() => {
		if (onedate) {
			(async () => {
				try {
					const { data } = await axios.post(
						`/dashboard_names_daywise?date=${moment(onedate).format(
							"YYYY-MM-DD"
						)}&blocks=${blocks}&error_percent=${one_error}`,
						{}
					);

					if (!data) return;
					setBlocked(false);
					setloading_show(false);

					const documentStyle = getComputedStyle(document.documentElement);

					// Prepare summary and name_object

					// Chart labels and keys
					const chartLabels = data[2];

					// Line/Bar Chart Data
					setChartData2({
						labels: chartLabels,
						datasets: [
							{
								type: "line",
								label: "Max % of Error",
								borderColor: documentStyle.getPropertyValue("--green-500"),
								backgroundColor: "rgba(34,197,94,0.15)",
								borderWidth: 3,
								pointBackgroundColor:
									documentStyle.getPropertyValue("--green-500"),
								pointBorderColor: "#fff",
								pointRadius: 7,
								pointHoverRadius: 10,
								pointStyle: "rectRounded",
								fill: false,
								tension: 0.45,
								data: data[3],
								yAxisID: "y1",
								order: 2,
							},
							{
								type: "bar",
								label: "Number of Tie-Lines with Error",
								backgroundColor: documentStyle.getPropertyValue("--blue-300"),
								borderColor: documentStyle.getPropertyValue("--blue-500"),
								borderWidth: 2,
								borderRadius: 8,
								barPercentage: 0.7,
								categoryPercentage: 0.6,
								data: data[1],
								order: 1,
							},
						],
					});

					const textColor = documentStyle.getPropertyValue("--text-color");
					const textColorSecondary = documentStyle.getPropertyValue(
						"--text-color-secondary"
					);
					const surfaceBorder =
						documentStyle.getPropertyValue("--surface-border");

					setChartOptions2({
						maintainAspectRatio: false,
						aspectRatio: 0.6,
						plugins: {
							legend: {
								labels: {
									color: textColor,
									font: { size: 15, weight: "bold" },
									usePointStyle: true,
									padding: 20,
								},
								position: "top",
								align: "center",
								onClick: (e, legendItem, legend) => {
									const ci = legend.chart;
									const index = legendItem.datasetIndex;
									const meta = ci.getDatasetMeta(index);
									meta.hidden =
										meta.hidden === null
											? !ci.data.datasets[index].hidden
											: null;
									ci.update();
								},
							},
							title: {
								display: true,
								text: "Tie-Lines Error Analysis Block-wise",
								color: textColor,
								font: { size: 20, weight: "bold" },
								padding: { top: 10, bottom: 30 },
							},
							tooltip: {
								enabled: true,
								mode: "nearest",
								intersect: false,
								backgroundColor: "#222",
								titleColor: "#fff",
								bodyColor: "#fff",
								borderColor: "#aaa",
								borderWidth: 1,
								padding: 12,
								caretSize: 8,
								displayColors: true,
								callbacks: {
									label: (context) => {
										// console.log(context);
										const idx = Number(context.label);
										// const key = chartKeys[idx];
										const display = "Block No: " + idx;
										const names = data[0][idx - 1] || [];

										if (context.dataset.type === "line") {
											return ["Max % of Error: " + context.parsed.y + "%"];
										} else {
											return [
												`${display} has ${context.parsed.y} Tie-Lines`,
												...names,
											];
										}
									},
								},
							},

							datalabels: {
								display: true,
								color: "#222",
								font: { weight: "bold", size: 13 },
								anchor: "end",
								align: "top",
								formatter: (value, ctx) => {
									if (ctx.dataset.type === "line") {
										return value + "%";
									}
									return value;
								},
							},
							zoom: {
								zoom: {
									wheel: { enabled: true },
									pinch: { enabled: true },
									mode: "xy",
								},
								pan: {
									enabled: true,
									mode: "xy",
								},
							},
						},
						hover: { mode: "nearest", intersect: true, animationDuration: 400 },
						animation: {
							duration: 1200,
							easing: "easeInOutQuart",
						},
						scales: {
							x: {
								title: {
									display: true,
									text: "Blocks",
									color: textColor,
									font: { size: 16, weight: "bold" },
								},
								ticks: {
									color: textColorSecondary,
									font: { size: 13, weight: "bold" },
									autoSkip: false,
									maxRotation: 30,
									minRotation: 0,
								},
								grid: {
									color: surfaceBorder,
									borderDash: [4, 4],
								},
							},
							y: {
								title: {
									display: true,
									text: "No. of Tie-Lines with Error",
									color: textColor,
									font: { size: 15, weight: "bold" },
								},
								type: "linear",
								display: true,
								position: "left",
								ticks: {
									color: textColorSecondary,
									font: { size: 13 },
									stepSize: 1,
									beginAtZero: true,
								},
								grid: {
									color: surfaceBorder,
									drawBorder: true,
									borderDash: [4, 4],
								},
							},
							y1: {
								title: {
									display: true,
									text: "% of Tie-Lines with Error",
									color: textColor,
									font: { size: 15, weight: "bold" },
								},
								type: "linear",
								display: true,
								position: "right",
								ticks: {
									color: textColorSecondary,
									font: { size: 13 },
									callback: (val) => val + "%",
									beginAtZero: true,
								},
								grid: {
									drawOnChartArea: false,
								},
							},
						},
						layout: {
							padding: {
								left: 10,
								right: 10,
								top: 10,
								bottom: 10,
							},
						},
						responsive: true,
						elements: {
							bar: {
								borderSkipped: false,
								borderRadius: 8,
							},
							point: {
								radius: 7,
								hoverRadius: 10,
								backgroundColor: documentStyle.getPropertyValue("--green-500"),
								borderColor: "#fff",
								borderWidth: 2,
							},
						},
					});
				} catch (error) {
					console.error(error);
				}
			})();
		}
	}, [onedate, blocks, one_error]);

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
			<div hidden={!loading_show}>
				<div className="loader">
					<div className="spinner"></div>
				</div>
			</div>

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
									maxDate={maxdate}
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
									style={{ width: "40vh", height: "40vh" }}
									className="w-auto"
								/>
							</div>
							<div className="chart-container">
								<Chart
									type="line"
									data={chartData1}
									options={chartOptions1}
									style={{ width: "120vh", height: "42vh" }}
								/>
							</div>
							{/* <div className="chart-label">
									Tie-Lines Error Analysis (Bar & Line Chart)
								</div> */}
						</div>
					</div>

					<Divider align="left" hidden={!page_hide}></Divider>

					<div className="charts-row">
						<label htmlFor="percent" className="font-bold block mb-2">
							Error Percent:
						</label>
						<InputNumber
							showButtons
							step={1}
							size={2}
							inputId="percent"
							value={one_error}
							onValueChange={(e) => setOneError(e.value)}
							suffix=" %"
							max={100}
							min={0}
						/>

						<label htmlFor="daterange" className="font-bold block mb-2">
							Date :
						</label>
						<Calendar
							showIcon
							value={onedate}
							onChange={(e) => setOnedate(e.value)}
							maxDate={maxdate}
							readOnlyInput
							hideOnDateTimeSelect
							dateFormat="dd-mm-yy"
							placeholder="Select Date"
						/>
					</div>
					<div className="charts-row">
						<div className="chart-container">
							<Chart
								type="line"
								data={chartData2}
								options={chartOptions2}
								style={{ width: "200vh", height: "70vh" }}
							/>
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
								// padding: 1rem 1.5rem;
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
