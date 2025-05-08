import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Avatar } from "primereact/avatar";
import { Container, Row, Col } from "react-grid-system";
import { Fieldset } from "primereact/fieldset";
import { Divider } from "primereact/divider";
import { Dropdown } from "primereact/dropdown";
import { InputTextarea } from "primereact/inputtextarea";
import { Checkbox } from "primereact/checkbox";
import { Button } from "primereact/button";
import { Toast } from "primereact/toast";
import {jwtDecode} from "jwt-decode";
import { useLocation } from "react-router-dom";
import { Dialog } from "primereact/dialog";
import moment from "moment";
import { FileUpload } from "primereact/fileupload";
import { Panel } from "primereact/panel";
import { Calendar } from "primereact/calendar";
import "../cssfiles/PasswordDemo.css";
import "primeflex/primeflex.css";
import { ProgressSpinner } from "primereact/progressspinner";
import "primereact/resources/primereact.min.css"; //core css
import "primeicons/primeicons.css"; //icons
import "../cssfiles/ButtonDemo.css";
import { MultiSelect } from "primereact/multiselect";
import { InputSwitch } from "primereact/inputswitch";
import { InputNumber } from "primereact/inputnumber";
import { Inplace, InplaceDisplay, InplaceContent } from "primereact/inplace";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import SCADAgraph from "../graphs/SCADAgraph";
import { Card } from "primereact/card";
import { Chart } from "primereact/chart";
import "../cssfiles/Animation.css";
import { BlockUI } from "primereact/blockui";
import zoomPlugin from "chartjs-plugin-zoom";
import { Chart as ChartJS, registerables } from "chart.js";

function Scada_Data(params) {
	const [start_date, setStart_Date] = useState();
	const [end_date, setEnd_Date] = useState();
	const [upload_visible, setupload_visible] = useState(false);
	const [scada_states, setscada_states] = useState();
	const [Selected_scada_states, setSelected_scada_states] = useState();
	const [date_range, setdate_range] = useState();
	const [scada_data, setscada_data] = useState();
	const [minutes, setminutes] = useState(15);
	const [graphenable, setgraphenable] = useState(true);
	const [chartData, setChartData] = useState({});
	const [chartOptions, setChartOptions] = useState({});
	const [blocked, setBlocked] = useState(false);
	const [loading_show, setloading_show] = useState(false);

	ChartJS.register(...registerables, zoomPlugin);

	const zoomOptions = {
		zoom: {
			wheel: {
				enabled: true,
			},
			pinch: {
				enabled: true,
			},
			mode: "xy",
		},
		pan: {
			enabled: true,
			mode: "xy",
		},
	};
	// </block>

	useEffect(() => {
		if (date_range && date_range[1]) {
			axios
				.post(
					"/getScadaCode?startDate=" +
						moment(date_range[0]).format("YYYY-MM-DD") +
						"&endDate=" +
						moment(date_range[1]).format("YYYY-MM-DD"),
					{}
				)
				.then((response) => {
					setscada_states(response.data);
					if (response.data.length === 0) {
						alert("Data not found, Please Upload");
						setupload_visible(true);
					} else {
						setupload_visible(false);
					}
				})
				.catch((error) => {});

			setEnd_Date(date_range[1]);
			setStart_Date(date_range[0]);
		}
	}, [date_range]);

	const uploaddata = () => {
		if (start_date && end_date) {
			axios
				.post(
					"/upload?startDate=" +
						moment(start_date).format("YYYY-MM-DD") +
						"&endDate=" +
						moment(end_date).format("YYYY-MM-DD")
				)
				.then((response) => {
					if (response.data === "Done") {
						alert(
							response.data +
								" Scada data inserted for " +
								moment(start_date).format("DD-MM-YYYY") +
								" to " +
								moment(end_date).format("DD-MM-YYYY")
						);
						setloading_show(false);
						setBlocked(false);
					} else {
						alert("File Insert Problem for: " + response.data);
						setloading_show(false);
						setBlocked(false);
					}
				})
				.catch((error) => {});
		} else {
			alert("Select Valid Date");
			setloading_show(false);
			setBlocked(false);
		}
	};
	const getSCADAdata = () => {
		if (start_date && end_date && Selected_scada_states) {
			axios
				.post(
					"/getScadaData?startDate=" +
						moment(start_date).format("YYYY-MM-DD") +
						"&endDate=" +
						moment(end_date).format("YYYY-MM-DD") +
						"&time=" +
						minutes +
						"&code=" +
						Selected_scada_states,
					{}
				)
				.then((response) => {
					setscada_data(response.data);
					// console.log(response.data);
					if (response.data.length > 1) {
						var temp_labels = [];

						for (var z = 1; z < response.data.length; z++) {
							let temp_labels1 = {
								label:
									"SCADA Data of " +
									response.data[z]["Code"] +
									": " +
									response.data[z]["Name"],
								data: response.data[z]["Data"],
								fill: false,
								// borderColor: documentStyle.getPropertyValue("--pink-500"),
								tension: 0.4,
								yAxisID: "y",
							};

							// console.log(temp_labels1);
							temp_labels.push(temp_labels1);
						}
						// console.log(temp_labels);
						const documentStyle = getComputedStyle(document.documentElement);
						const textColor = documentStyle.getPropertyValue("--text-color");
						const textColorSecondary = documentStyle.getPropertyValue(
							"--text-color-secondary"
						);
						const surfaceBorder =
							documentStyle.getPropertyValue("--surface-border");
						const data = {
							labels: response.data[0],
							datasets: temp_labels,
						};
						const options = {
							stacked: false,
							maintainAspectRatio: false,
							aspectRatio: 0.6,
							plugins: {
								zoom: zoomOptions,
								legend: {
									labels: {
										color: textColor,
									},
								},
							},
							scales: {
								x: {
									ticks: {
										color: textColorSecondary,
									},
									grid: {
										color: surfaceBorder,
									},
								},
								y: {
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
							},
						};

						setChartData(data);
						setChartOptions(options);
					}
					setloading_show(false);
					setBlocked(false);
				})
				.catch((error) => {});

			setgraphenable(false);
		}
	};

	// const getSCADAgraph = () => {
	// 	if (scada_data) {
	// 	}
	// };

	return (
		<>
			<div hidden={!loading_show}>
				<div className="loader">
					<div className="spinner"></div>
				</div>
			</div>

			<BlockUI blocked={blocked} fullScreen />

			{/* <img src="GI-Logo.png"></img> */}
			{/* <div className="card">
				<ProgressSpinner
					style={{
						width: "100px",
						height: "100px",
						alignItems: "center",
						backgroundImage: "GI-Logo.png",
					}}
					strokeWidth="5"
					// fill="GI-Logo.png"
					animationDuration="1s"
				/>
			</div>
			<img src="GI-Logo.png"></img> */}
			<Divider align="left">
				<span
					className="p-tag"
					style={{ backgroundColor: "#dc2626", fontSize: "large" }}
				>
					<Avatar
						icon="pi pi-bolt"
						style={{ backgroundColor: "#dc2626", color: "#ffffff" }}
						shape="square"
					/>
					SCADA Tab
				</span>
			</Divider>
			<div className="flex flex-wrap gap-1 justify-content-between align-items-center">
				<div className="field"></div>
				<div className="field">
					<label htmlFor="range">Date Range:</label> <br />
					<Calendar
						placeholder="Select Date Range"
						dateFormat="dd/mm/yy"
						value={date_range}
						onChange={(e) => setdate_range(e.value)}
						showIcon
						selectionMode="range"
						readOnlyInput
					/>
				</div>

				<div className="field">
					<label htmlFor="range">Interval (1 to 1440 minutes)</label>
					<br />
					<InputNumber
						// tooltip="Select Data Interval"
						size={7}
						min={15}
						max={1440}
						step={15}
						value={minutes}
						onValueChange={(e) => setminutes(e.value)}
						suffix=" minutes"
						showButtons
						buttonLayout="horizontal"
						decrementButtonClassName="p-button-danger"
						incrementButtonClassName="p-button-success"
						incrementButtonIcon="pi pi-plus"
						decrementButtonIcon="pi pi-minus"
					/>
				</div>
				<div className="field">
					<label htmlFor="range">Select Station : </label>
					<br />
					<MultiSelect
						// tooltip="Select SCADA Station"
						filterPlaceholder="Search SCADA Station"
						showSelectAll
						showClear
						resetFilterOnHide
						maxSelectedLabels={5}
						selectionLimit={5}
						display="chip"
						placeholder="Select SCADA Station(s)"
						value={Selected_scada_states}
						options={scada_states}
						onChange={(e) => setSelected_scada_states(e.value)}
						filter
					/>
				</div>
				<div className="field">
					<Button
						severity="danger"
						raised
						rounded
						label="Get SCADA Data"
						className="p-button-help"
						style={{
							width: "auto",
							float: "center",
							backgroundColor: "#dc2626",
						}}
						onClick={() => {
							setBlocked(true);
							setloading_show(true);
							getSCADAdata();
							// getSCADAgraph();
						}}
					/>
				</div>
				<div className="field" hidden={!upload_visible}>
					<Button
						raised
						// tooltip="Upload Scada Files"
						icon="pi pi-upload"
						rounded
						severity="success"
						aria-label="Notification"
						onClick={() => {
							setBlocked(true);
							setloading_show(true);
							uploaddata();
						}}
					/>
					<br />
					<label htmlFor="range">Upload </label>
				</div>
				<div className="field"></div>
			</div>

			<div hidden={graphenable}>
				<br />
				<Divider align="center">
					<span
						className="p-tag"
						style={{ backgroundColor: "#000000", fontSize: "large" }}
					>
						SCADA Graph
					</span>
				</Divider>
				<div className="card">
					<Chart type="line" data={chartData} options={chartOptions} />
				</div>
			</div>
		</>
	);
}
export default Scada_Data;
