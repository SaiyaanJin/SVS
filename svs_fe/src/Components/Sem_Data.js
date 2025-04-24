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
import { BlockUI } from "primereact/blockui";
import "primereact/resources/primereact.min.css"; //core css
import "primeicons/primeicons.css"; //icons
import "../cssfiles/ButtonDemo.css";
import { MultiSelect } from "primereact/multiselect";
import { InputSwitch } from "primereact/inputswitch";
import { InputNumber } from "primereact/inputnumber";
import { Inplace, InplaceDisplay, InplaceContent } from "primereact/inplace";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import Metergraph from "../graphs/Metergraph";
import { Card } from "primereact/card";
import { Chart } from "primereact/chart";
import zoomPlugin from "chartjs-plugin-zoom";
import { Chart as ChartJS, registerables } from "chart.js";

function Sem_Data(params) {
	const toast = useRef();
	const [File, setFile] = useState([]);
	const [start_date, setstart_date] = useState();
	const [end_date, setend_date] = useState();
	const [meter_number, setmeter_number] = useState();
	const [selected_meter_number, setselected_meter_number] = useState();
	const [time, settime] = useState(15);
	const [date_range, setdate_range] = useState();
	const [graphenable, setgraphenable] = useState(true);
	const [uploadenable, setuploadenable] = useState(true);
	const [folder_files, setfolder_files] = useState(false);
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
					"http://10.3.230.62:5003/meter_names?startDate=" +
						moment(date_range[0]).format("YYYY-MM-DD") +
						"&endDate=" +
						moment(date_range[1]).format("YYYY-MM-DD") +
						"&time=" +
						time +
						"&folder=no",
					{}
				)
				.then((response) => {
					setmeter_number(response.data);
					setfolder_files(false);
					setuploadenable(true);
					if (response.data.length === 0) {
						axios
							.post(
								"http://10.3.230.62:5003/meter_names?startDate=" +
									moment(date_range[0]).format("YYYY-MM-DD") +
									"&endDate=" +
									moment(date_range[1]).format("YYYY-MM-DD") +
									"&time=" +
									time +
									"&folder=yes",
								{}
							)
							.then((response) => {
								if (response.data[0] === "Please Upoad") {
									alert("Data not found anywhere, Please Upload");
									setuploadenable(false);
								} else {
									setmeter_number(response.data);
									setfolder_files(true);
								}
							})
							.catch((error) => {});
					}
				})
				.catch((error) => {});

			setend_date(date_range[1]);
			setstart_date(date_range[0]);
		}
	}, [date_range]);

	const showSuccess = (v) => {
		toast.current.show({
			severity: "success",
			summary: v,
			detail: v + " SuccessFully",
			life: 3000,
		});
	};

	const reject = (v) => {
		toast.current.show({
			severity: "error",
			summary: "Error",
			detail: v,
			life: 3000,
		});
	};

	const file_name = (e) => {
		var filenames = [];
		for (var i = 0; i < e.files.length; i++) {
			filenames = [...filenames, ...[e.files[i].name]];
		}

		setFile([...File, ...filenames]);
		if (filenames) {
			showSuccess("SEM File Uploaded");
			// reject("Upload Error");
			setuploadenable(true);
		}
	};

	const upload_error = (e) => {
		reject("Upload Error");
	};

	const getmeterdata = () => {
		if (start_date && end_date && selected_meter_number) {
			if (!folder_files) {
				axios
					.post(
						"http://10.3.230.62:5003/GetMeterData?startDate=" +
							moment(start_date).format("YYYY-MM-DD") +
							"&endDate=" +
							moment(end_date).format("YYYY-MM-DD") +
							"&meter=" +
							selected_meter_number +
							"&time=" +
							time +
							"&folder=no",
						{}
					)
					.then((response) => {
						// setmeter_data(response.data);
						setgraphenable(false);
						setloading_show(false);
						setBlocked(false);
						if (response.data.length > 1) {
							var temp_labels = [];

							for (var z = 1; z < response.data.length; z++) {
								let temp_labels1 = {
									label:
										"SEM Data of " +
										response.data[z]["meterNO"] +
										": " +
										response.data[z]["meterID"],
									data: response.data[z]["data"],
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
					});
			} else {
				axios
					.post(
						"http://10.3.230.62:5003/GetMeterData?startDate=" +
							moment(start_date).format("YYYY-MM-DD") +
							"&endDate=" +
							moment(end_date).format("YYYY-MM-DD") +
							"&meter=" +
							selected_meter_number +
							"&time=" +
							time +
							"&folder=yes",
						{}
					)
					.then((response) => {
						// setmeter_data(response.data);
						setgraphenable(false);
						setloading_show(false);
						setBlocked(false);

						if (response.data.length > 1) {
							var temp_labels = [];

							for (var z = 1; z < response.data.length; z++) {
								let temp_labels1 = {
									label:
										"SEM Data of " +
										response.data[z]["meterNO"] +
										": " +
										response.data[z]["meterID"],
									data: response.data[z]["data"],
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
					});
			}
		}
	};

	return (
		<>
			<div hidden={!loading_show}>
				<div className="loader">
					<div className="spinner"></div>
				</div>
			</div>

			<BlockUI blocked={blocked} fullScreen />

			<Toast ref={toast} />

			<Divider align="left">
				<span
					className="p-tag"
					style={{ backgroundColor: "#065fc8", fontSize: "large" }}
				>
					<Avatar
						icon="pi pi-calculator"
						style={{ backgroundColor: "#065fc8", color: "#ffffff" }}
						shape="square"
					/>
					SEM/Meter Data Tab
				</span>
			</Divider>
			<div className="grid">
				<div hidden={uploadenable} className="col">
					<label htmlFor="range">Upload AMR Data</label> <br />
					<FileUpload
						name="demo[]"
						onUpload={file_name}
						onError={upload_error}
						url="http://10.3.230.62:5003/file_upload"
						accept="zip/*"
						maxFileSize={50000000}
						emptyTemplate={
							<p className="m-0">
								Drag and drop relevant files supporting the issue.
							</p>
						}
					/>
				</div>
			</div>
			<br />

			<div className="flex flex-wrap gap-1 justify-content-between align-items-center">
				<div className="field"> </div>
				<div className="field">
					<span className="p-float-label">
						Date Range:
						<br />
						<Calendar
							placeholder="Select Date Range"
							dateFormat="dd/mm/yy"
							value={date_range}
							onChange={(e) => setdate_range(e.value)}
							showIcon
							selectionMode="range"
							readOnlyInput
						/>
					</span>
				</div>

				{/* <div className="col">
					{" "}
					<div className="field col-12 md:col-6" style={{ marginLeft: "-20%" }}>
						<label htmlFor="range">To</label> <br />
						<Calendar
							showIcon
							showWeek
							// showTime
							// hourFormat="24"
							// hideOnDateTimeSelect
							placeholder="End Date"
							dateFormat="dd-mm-yy"
							value={end_date}
							onChange={(e) => {
								setend_date(e.value);
							}}
							// onClick={() => {
							//   DemandNames();
							// }}
							monthNavigator
							yearNavigator
							yearRange="2010:2025"
							showButtonBar
						></Calendar>
					</div>
				</div> */}
				<div className="field">
					<span className="p-float-label">
						Interval (1 to 1440 minutes)
						<br />
						<InputNumber
							size={10}
							min={15}
							max={1440}
							step={15}
							value={time}
							onValueChange={(e) => settime(e.value)}
							suffix=" minutes"
							showButtons
							buttonLayout="horizontal"
							decrementButtonClassName="p-button-danger"
							incrementButtonClassName="p-button-success"
							incrementButtonIcon="pi pi-plus"
							decrementButtonIcon="pi pi-minus"
						/>
					</span>
				</div>
				<div className="field">
					<span className="p-float-label">
						Select Meter:
						<br />
						<MultiSelect
							filterPlaceholder="Search here"
							showSelectAll
							showClear
							resetFilterOnHide
							maxSelectedLabels={5}
							selectionLimit={5}
							display="chip"
							placeholder="meter number (meter id)"
							value={selected_meter_number}
							options={meter_number}
							onChange={(e) => setselected_meter_number(e.value)}
							filter
						/>
					</span>
				</div>

				<div className="field">
					<Button
						severity="success"
						raised
						rounded
						label="Get Meter Data"
						icon="pi pi-bookmark"
						onClick={() => {
							setBlocked(true);
							setloading_show(true);
							getmeterdata();
						}}
						autoFocus
					/>
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
						SEM/Meter Graph
					</span>
				</Divider>
				<div className="card">
					<Chart type="line" data={chartData} options={chartOptions} />
				</div>
			</div>
		</>
	);
}
export default Sem_Data;
