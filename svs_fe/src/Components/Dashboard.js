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
import { Skeleton } from "primereact/skeleton";
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
	const [loading_show, setloading_show] = useState(true);

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
							`T-L with Diff. (${data.total_count[0]})`,
							`T-L within Reasonable Diff. (${
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
								text: "Tie-Lines Summary (332 Tie-Lines)",
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
					console.log(name_object);
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
								label: "% of Tie-Lines with Difference",
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
								label: "To-End Tie-Lines with Difference",
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
								label: "Far End Tie-Lines with Difference",
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
								text: "SEM vs SCADA Difference Analysis Constituent-Wise",
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
												"% of Tie-Line with Difference: " +
													context.parsed.y +
													"%",
											];
										} else {
											if (
												context.dataset.label ===
												"To-End Tie-Lines with Difference"
											) {
												const names1 = name_object[key][0] || [];
												return [
													`${display} To End has: ${context.parsed.y} Tie-Lines`,
													...names1,
												];
											} else {
												const names2 = name_object[key][1] || [];
												return [
													`${display} Far End has: ${context.parsed.y} Tie-Lines`,
													...names2,
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
									text: "No. of Tie-Lines with Difference",
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
									text: "% of Tie-Lines with Difference",
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
		setBlocked(true);
		setloading_show(false);
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
					setloading_show(true);

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
								label: "Max % of Difference",
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
								label: "Number of Tie-Lines with Difference",
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
								text: "SEM vs SCADA Difference Analysis Block-Wise",
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
											return ["Max % of Difference: " + context.parsed.y + "%"];
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
									text: "No. of Tie-Lines with Difference",
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
									text: "% of Tie-Lines with Difference",
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
				setloading_show(true);
			})
			.catch((error) => {});
	};

	return (
		<>
			{/* Loader Overlay */}
			{!loading_show && (
				<div
					className="loader-overlay"
					aria-busy="true"
					aria-label="Loading content"
				>
					<div
						className="loader"
						role="alert"
						aria-live="assertive"
						aria-atomic="true"
					>
						<div className="spinner spinner-shadow">
							{/* <div className="spinner-half spinner-blue"></div>
							<div className="spinner-half spinner-orange"></div> */}
						</div>
						<span className="visually-hidden">Loading...</span>
					</div>
				</div>
			)}

			<BlockUI blocked={blocked} fullScreen />

			{/* Login Prompt */}
			{page_hide && (
				<div className="centered-content" style={{ minHeight: 300 }}>
					<Fieldset
						legend="Session Expired"
						className="session-expired-fieldset"
					>
						<div
							className="login-prompt-content"
							style={{ textAlign: "center" }}
						>
							<Avatar
								icon="pi pi-user"
								className="avatar-error"
								shape="circle"
								aria-label="User Icon"
							/>
							<h2 className="session-expired-text" tabIndex={0}>
								Please Login again via SSO
							</h2>
						</div>
					</Fieldset>
				</div>
			)}

			{/* Welcome Banner */}
			{!page_hide && (
				// <section
				// 	className="welcome-banner"
				// 	aria-live="polite"
				// 	aria-atomic="true"
				// 	aria-label="Welcome message"
				// >
				<span
					className="scrolling-text"
					tabIndex={0}
					style={{ marginTop: "1rem", marginBottom: "-1rem" }}
				>
					Welcome&nbsp;
					<strong>
						Sh. {Person_Name} ({User_id})
					</strong>
					&nbsp;of&nbsp;<strong>{Department}</strong>
				</span>
				// </section>
			)}

			{/* Dashboard Info */}
			<Divider align="left" hidden={page_hide} style={{ marginTop: "-4%" }}>
				<span className="dashboard-header">
					{/* <Avatar
						icon="pi pi-Home"
						shape="square"
						className="dashboard-header-avatar"
						aria-hidden="true"
					/> */}
					Dashboard
				</span>
			</Divider>

			{/* Dashboard Info (unchanged) */}
			{!page_hide && (
				<section
					className="dashboard-info-row"
					aria-label="Dashboard info section"
				>
					<div
						className="dashboard-info-item"
						tabIndex={0}
						role="group"
						aria-label="Scada DB Up-To:"
					>
						<Avatar
							icon="pi pi-database"
							style={{
								backgroundColor: "#1976d2",
								color: "#fff",
								marginRight: 12,
							}}
							aria-hidden="true"
						/>
						<div>
							<span className="info-label">Scada DB Up-To:</span>
							<div className="info-value">{scada_db_date?.Date || "-"}</div>
						</div>
					</div>
					<div
						className="dashboard-info-item"
						tabIndex={0}
						role="group"
						aria-label="Meter DB Up-To:"
					>
						<Avatar
							icon="pi pi-server"
							style={{
								backgroundColor: "#388e3c",
								color: "#fff",
								marginRight: 12,
							}}
							aria-hidden="true"
						/>
						<div>
							<span className="info-label">Meter DB Up-To:</span>
							<div className="info-value">{meter_date?.date || "-"}</div>
						</div>
					</div>
					<div
						className="dashboard-info-item"
						tabIndex={0}
						role="group"
						aria-label="Meter Folder Up-To:"
					>
						<Avatar
							icon="pi pi-folder-open"
							style={{
								backgroundColor: "#fbc02d",
								color: "#fff",
								marginRight: 12,
							}}
							aria-hidden="true"
						/>
						<div>
							<span className="info-label">Meter Folder Up-To:</span>
							<div className="info-value">
								{meter_folder_date && meter_folder_date.length > 0
									? meter_folder_date[0].meter_folder_date
									: "-"}
							</div>
						</div>
					</div>
					<div className="dashboard-info-item">
						<Button
							size="small"
							rounded
							raised
							severity="danger"
							label="Delete Folder Files"
							icon="pi pi-trash"
							onClick={() => {
								folder_delete();
								setBlocked(true);
								setloading_show(false);
							}}
							style={{ minWidth: 160, fontWeight: 600 }}
							aria-label="Delete Folder Files"
						/>
					</div>
				</section>
			)}

			{/* Charts Section with your 4 rows layout */}
			{!page_hide && (
				<section
					className="charts-section"
					aria-label="Charts and controls"
					style={{ marginTop: "-3%" }}
				>
					{/* Row 1: Main chart controls */}
					<div className="charts-controls-row" style={{ marginTop: "-1.5%" }}>
						<div className="charts-control">
							<label htmlFor="percent" className="font-bold block mb-2">
								Percent Difference:
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
								style={{ width: 120 }}
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
								style={{ width: 140 }}
							/>
						</div>

						<div className="charts-control" style={{ minWidth: 180 }}>
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
								style={{ width: "50%" }}
							/>
						</div>
					</div>

					{/* Row 2: Two charts side by side */}
					<div className="charts-visuals-row" style={{ marginTop: "-3%" }}>
						<div className="chart-container">
							<Chart
								type="pie"
								data={chartData}
								options={chartOptions}
								style={{ width: "30vh", height: "40vh" }}
							/>
						</div>

						<div className="chart-container">
							<Chart
								type="line"
								data={chartData1}
								options={chartOptions1}
								style={{ width: "150vh", height: "40vh" }}
							/>
						</div>
					</div>

					{/* Row 3: Secondary controls horizontally */}

					{/* Row 4: Full width block-wise error analysis chart */}
					<div
						className="blockwise-chart-container"
						style={{ marginTop: "-1.5%" }}
					>
						<div className="charts-controls-row secondary-controls">
							<div className="charts-control">
								<label htmlFor="percent2" className="font-bold block mb-2">
									Percent Difference:
								</label>
								<InputNumber
									showButtons
									step={1}
									size={2}
									inputId="percent2"
									value={one_error}
									onValueChange={(e) => setOneError(e.value)}
									suffix=" %"
									max={100}
									min={0}
									style={{ width: 120 }}
								/>
							</div>

							<div className="charts-control" style={{ minWidth: 160 }}>
								<label htmlFor="onedate" className="font-bold block mb-2">
									Date:
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
									inputId="onedate"
									style={{ width: "100%" }}
								/>
							</div>
						</div>
						<Chart
							type="line"
							data={chartData2}
							options={chartOptions2}
							style={{
								width: "100%",
								height: "60vh",
								minWidth: 400,
								marginTop: "-2%",
							}}
						/>
					</div>
				</section>
			)}

			{/* CSS */}
			<style jsx>{`
				.loader-overlay {
					position: fixed;
					top: 0;
					left: 0;
					right: 0;
					bottom: 0;
					background: rgba(255, 255, 255, 0.9);
					z-index: 9999;
					display: flex;
					align-items: center;
					justify-content: center;
					backdrop-filter: blur(6px);
				}
				.loader {
					display: flex;
					align-items: center;
					justify-content: center;
					height: 100vh;
				}
				.spinner {
					position: relative;
					width: 225px;
					height: 225px;
					display: flex;
					align-items: center;
					justify-content: center;
				}
				.spinner-shadow {
					box-shadow: 0 0 30px 10px #1976d2,
						0 8px 40px 0 rgba(25, 118, 210, 0.25),
						0 1.5px 8px 0 rgba(0, 0, 0, 0.08);
				}
				.spinner-half {
					position: absolute;
					top: 0;
					left: 0;
					width: 210px;
					height: 210px;
					border-radius: 50%;
					border: 8px solid transparent;
					border-top: 8px solid;
					animation: spin 1.1s linear infinite;
				}
				// .spinner-blue {
				// 	border-top-color: #1976d2;
				// 	z-index: 2;
				// 	animation-delay: 0s;
				// }
				// .spinner-orange {
				// 	border-top-color: #ff9800;
				// 	z-index: 1;
				// 	animation-delay: 0.55s;
				// }
				@keyframes spin {
					0% {
						transform: rotate(0deg);
					}
					100% {
						transform: rotate(360deg);
					}
				}

				.centered-content {
					display: flex;
					justify-content: center;
					align-items: center;
					min-height: 180px;
					padding: 1rem;
				}
				.session-expired-fieldset {
					max-width: 380px;
					margin: auto;
					// box-shadow: 0 3px 14px rgba(244, 67, 54, 0.3);
					border-radius: 14px;
					border: 1px solid #f44336;
				}
				.avatar-error {
					background-color: #f44336 !important;
					color: #fff !important;
					margin-bottom: 16px;
					width: 64px !important;
					height: 64px !important;
				}
				.session-expired-text {
					margin: 0;
					color: #f44336;
					font-weight: 700;
				}

				.welcome-banner {
					width: 100%;
					overflow: hidden;
					background: linear-gradient(90deg, #e3f2fd 0%, #fce4ec 100%);
					padding: 0.8rem 0;
					border-radius: 16px;
					margin-bottom: 2rem;
					// box-shadow: 0 3px 18px rgba(0, 0, 0, 0.07);
					font-size: 1.25rem;
					font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
					color: #222;
				}
				.scrolling-text {
					display: inline-block;
					padding-left: 100%;
					white-space: nowrap;
					animation: scroll-left 16s linear infinite;
					font-weight: 600;
					letter-spacing: 0.6px;
				}
				.scrolling-text:focus {
					animation-play-state: paused;
					outline: 2px solid #1976d2;
					border-radius: 4px;
				}
				@keyframes scroll-left {
					0% {
						transform: translateX(0);
					}
					100% {
						transform: translateX(-100%);
					}
				}

				.dashboard-header,
				.charts-header {
					background: linear-gradient(90deg, #1976d2 0%, #d81b60 100%);
					font-size: 1.3rem;
					color: #fff;
					border-radius: 10px;
					padding: 0.5rem 1.6rem;
					font-weight: 700;
					display: inline-flex;
					align-items: center;
					gap: 10px;
					// box-shadow: 0 3px 14px rgba(216, 27, 96, 0.3);
					user-select: none;
				}
				.dashboard-header-avatar,
				.charts-header-avatar {
					background-color: #fff !important;
					color: inherit !important;
					width: 36px !important;
					height: 36px !important;
				}

				.dashboard-info-row {
					display: flex;
					// flex-wrap: wrap;
					justify-content: flex-start;
					gap: 15%;
					margin-bottom: 2rem;
					margin-top: -2rem;
					// background: linear-gradient(90deg, #f5f7fa 0%, #e3f0ff 100%);
					padding: 1.5rem 2.5rem;
					border-radius: 18px;
					// box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
					transition: background 0.3s ease;
				}
				.dashboard-info-row:hover {
					// background: linear-gradient(90deg, #eaf3ff 0%, #fce4ec 100%);
				}

				.dashboard-info-item {
					display: flex;
					align-items: center;
					gap: 1rem;
					min-width: 240px;
					font-size: 1.1rem;
					background: #fff;
					padding: 1rem 1.6rem;
					border-radius: 14px;
					// box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
					transition: box-shadow 0.3s ease;
					cursor: default;
				}
				.dashboard-info-item:focus-within,
				.dashboard-info-item:hover {
					// box-shadow: 0 6px 20px rgba(25, 118, 210, 0.3);
				}
				.info-label {
					font-weight: 700;
					color: #1976d2;
					font-size: 1rem;
				}
				.info-value {
					font-size: 1.15rem;
					color: #222;
					font-weight: 600;
				}

				.charts-section {
					background: linear-gradient(90deg, #f5f7fa 0%, #e3f0ff 100%);
					padding: 2.5rem 1.5rem;
					border-radius: 18px;
					// box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
					margin-bottom: 3rem;
					display: flex;
					flex-direction: column;
					gap: 2.5rem;
				}

				/* Row 1 & Row 3 controls style */
				.charts-controls-row {
					display: flex;
					flex-wrap: nowrap;
					gap: 2rem;
					justify-content: flex-start;
					align-items: flex-end;
					background: #fff;
					padding: 1.5rem 2rem;
					border-radius: 14px;
					// box-shadow: 0 3px 14px rgba(0, 0, 0, 0.04);
					max-width: 100%;
					overflow-x: auto;
				}

				.charts-controls-row.secondary-controls {
					max-width: 400px; /* smaller row for second controls */
				}

				.charts-control {
					flex: 1 1 auto;
					min-width: 140px;
					margin-bottom: 0;
				}

				.charts-control label {
					display: block;
					margin-bottom: 0.4rem;
					font-weight: 700;
					color: #1976d2;
				}

				/* Row 2: charts side by side */
				.charts-visuals-row {
					display: flex;
					flex-wrap: nowrap;
					gap: 2.5rem;
					justify-content: center;
					align-items: flex-start;
				}

				.chart-container {
					flex: 1 1 auto;
					min-width: 320px;
					background: #fff;
					padding: 1.5rem 2rem;
					border-radius: 14px;
					// box-shadow: 0 3px 14px rgba(0, 0, 0, 0.04);
					transition: box-shadow 0.3s ease;
				}

				.chart-container:hover {
					box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
				}

				.chart-title {
					text-align: center;
					margin-bottom: 1rem;
					font-weight: 700;
					font-size: 1.15rem;
					color: #1976d2;
					letter-spacing: 0.5px;
				}

				/* Row 4: blockwise chart full width */
				.blockwise-chart-container {
					background: #fff;
					border-radius: 14px;
					padding: 1.5rem 2rem;
					// box-shadow: 0 3px 14px rgba(0, 0, 0, 0.04);
					min-width: 320px;
				}

				/* Responsive adjustments */
				@media (max-width: 900px) {
					.charts-controls-row,
					.charts-controls-row.secondary-controls {
						flex-wrap: wrap;
						gap: 1.5rem;
						justify-content: center;
					}
					.charts-control {
						min-width: 100%;
					}
					.charts-visuals-row {
						flex-wrap: wrap;
					}
					.chart-container,
					.blockwise-chart-container {
						width: 100% !important;
						min-width: unset;
					}
				}

				.card {
					background: #fff;
					border-radius: 16px;
					padding: 1rem 2rem;
					// box-shadow: 0 4px 25px rgba(0, 0, 0, 0.06);
				}

				/* Utility classes */
				.visually-hidden {
					position: absolute !important;
					height: 1px;
					width: 1px;
					overflow: hidden;
					clip: rect(1px, 1px, 1px, 1px);
					white-space: nowrap;
				}
			`}</style>
		</>
	);
}
export default Dashboard;
