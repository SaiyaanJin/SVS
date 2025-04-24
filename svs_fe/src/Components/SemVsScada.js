import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Avatar } from "primereact/avatar";
import { Button } from "primereact/button";
import { Toast } from "primereact/toast";
import { Dialog } from "primereact/dialog";
import moment from "moment";
import { Calendar } from "primereact/calendar";
import { InputNumber } from "primereact/inputnumber";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Chart } from "primereact/chart";
import { Chart as ChartJS, registerables } from "chart.js";
import { useNavigate } from "react-router-dom";
import { FilterMatchMode, FilterOperator } from "primereact/api";
import { InputText } from "primereact/inputtext";
import { Skeleton } from "primereact/skeleton";
import { RadioButton } from "primereact/radiobutton";
import "../cssfiles/Animation.css";
import "../cssfiles/PasswordDemo.css";
import "primeflex/primeflex.css";
import "primereact/resources/themes/lara-light-indigo/theme.css"; //theme
import "primereact/resources/primereact.min.css"; //core css
import "primeicons/primeicons.css"; //icons
import "../cssfiles/ButtonDemo.css";
import { InputSwitch } from "primereact/inputswitch";
import { BlockUI } from "primereact/blockui";
import { Divider } from "primereact/divider";
import zoomPlugin from "chartjs-plugin-zoom";


function SemVsScada(params) {
	const items = Array.from({ length: 14 }, (v, i) => i);
	const toast = useRef();
	var navigate = new useNavigate();
	const dt = useRef(null);
	const [offset, setoffset] = useState(20);
	const [date_range, setdate_range] = useState();
	const [start_date, setStart_Date] = useState();
	const [end_date, setEnd_Date] = useState();
	const [graph_header, setgraph_header] = useState("");
	const [table_header, settable_header] = useState("");
	const minutes = 15;
	const [invert, setinvert] = useState(false);
	const [show_table, setshow_table] = useState(true);
	const [folder_files, setfolder_files] = useState(false);
	const [chartData1, setChartData1] = useState({});
	const [chartOptions1, setChartOptions1] = useState({});
	const [svs_report, setsvs_report] = useState([]);
	const [error_names, seterror_names] = useState([]);
	const [svs_report_copy, setsvs_report_copy] = useState();
	const [to_end_graph, setto_end_graph] = useState(true);
	const [far_end_graph, setfar_end_graph] = useState(true);
	const [show_Skeleton, setshow_Skeleton] = useState(false);
	const [globalFilterValue, setGlobalFilterValue] = useState("");
	const [rowgraph, setrowgraph] = useState(false);
	const [To_table_val, setTo_table_val] = useState();
	const [Far_table_val, setFar_table_val] = useState();
	const [original_data, setoriginal_data] = useState();
	const [FeederFrom, setFeederFrom] = useState("All");
	const [blocked, setBlocked] = useState(false);
	const [loading_show, setloading_show] = useState(false);
	const [selectedrows, setselectedrows] = useState([]);
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

	const [filters, setFilters] = useState({
		global: { value: null, matchMode: FilterMatchMode.CONTAINS },
		Feeder_Name: { value: null, matchMode: FilterMatchMode.CONTAINS },
		to_end_avg_val: {
			operator: FilterOperator.OR,
			constraints: [
				{
					value: 0,
					matchMode: FilterMatchMode.GREATER_THAN_OR_EQUAL_TO,
				},
			],
		},
		far_end_avg_val: {
			operator: FilterOperator.OR,
			constraints: [
				{
					value: 0,
					matchMode: FilterMatchMode.GREATER_THAN_OR_EQUAL_TO,
				},
			],
		},
		scada_avg: {
			operator: FilterOperator.OR,
			constraints: [
				{
					value: 0,
					matchMode: FilterMatchMode.GREATER_THAN_OR_EQUAL_TO,
				},
			],
		},
		sem_avg: {
			operator: FilterOperator.OR,
			constraints: [
				{
					value: 0,
					matchMode: FilterMatchMode.GREATER_THAN_OR_EQUAL_TO,
				},
			],
		},
		// far_end_max_val: { operator: FilterOperator.OR, constraints: [{ value: 0, matchMode: FilterMatchMode.EQUALS }] },
	});

	const bodyTemplate = () => {
		return <Skeleton></Skeleton>;
	};

	useEffect(() => {
		if (date_range && date_range[1]) {
			// var date_range = [];
			// if (start_date[1] === null) {
			// 	date_range.push(moment(date[0]).format("DD-MM-YYYY"));
			// 	date_range.push(moment(date[0]).format("DD-MM-YYYY"));
			// } else {
			// 	date_range.push(moment(date[0]).format("DD-MM-YYYY"));
			// 	date_range.push(moment(date[1]).format("DD-MM-YYYY"));
			// }

			axios
				.post(
					"http://10.3.230.62:5003/meter_check?startDate=" +
						moment(date_range[0]).format("YYYY-MM-DD") +
						"&endDate=" +
						moment(date_range[1]).format("YYYY-MM-DD"),
					{}
				)
				.then((response) => {
					if (response.data[0] === "Database") {
						setfolder_files(false);
					}

					if (response.data[0] === "Folder") {
						setfolder_files(true);
					}

					if (response.data[0] === "Some") {
						setfolder_files(false);
						alert("Meter Data for some dates not found:" + response.data[0]);
					}

					if (response.data[0] === "Nowhere") {
						reject("Data not found");
						if (
							window.confirm(
								"Data not found anywhere, Please Upload in Meter Data tab"
							)
						) {
							navigate("/Sem_Data");
						}
					}
				})
				.catch((error) => {});

			setEnd_Date(date_range[1]);
			setStart_Date(date_range[0]);
		}
	}, [date_range]);
	// console.log(folder_files);
	useEffect(() => {
		if (svs_report_copy) {
			var temp_Original_Api_data = svs_report_copy;
			if (FeederFrom === "All") {
				setsvs_report(temp_Original_Api_data);
			} else {
				var temp_data = [];
				for (var z = 0; z < temp_Original_Api_data.length; z++) {
					if (
						temp_Original_Api_data[z]["Feeder_From"] === FeederFrom ||
						temp_Original_Api_data[z]["To_Feeder"] === FeederFrom
					) {
						temp_data.push(temp_Original_Api_data[z]);
					}
				}
				setsvs_report(temp_data);
			}
		}
	}, [FeederFrom]);

	const getSEMvsSCADAreport = () => {
		if (start_date && end_date) {
			setshow_table(true);
			setshow_Skeleton(true);
			if (!folder_files) {
				axios
					.post(
						"http://10.3.230.62:5003/SEMvsSCADAreport?startDate=" +
							moment(start_date).format("YYYY-MM-DD") +
							"&endDate=" +
							moment(end_date).format("YYYY-MM-DD") +
							"&time=" +
							minutes +
							"&folder=no" +
							"&offset=" +
							offset,
						{}
					)
					.then((response) => {
						
						seterror_names(response.data[1]);
						setoriginal_data(response.data[0]);
						setsvs_report(response.data[0].Data);
						setsvs_report_copy(response.data[0].Data);

						if (response.data) {
							setshow_table(false);
							setshow_Skeleton(false);
							setBlocked(false);
							setloading_show(false);
						}
					});
			} else {
				axios
					.post(
						"http://10.3.230.62:5003/SEMvsSCADAreport?startDate=" +
							moment(start_date).format("YYYY-MM-DD") +
							"&endDate=" +
							moment(end_date).format("YYYY-MM-DD") +
							"&time=" +
							minutes +
							"&folder=yes" +
							"&offset=" +
							offset,
						{}
					)
					.then((response) => {
						
						seterror_names(response.data[1]);
						setoriginal_data(response.data[0]);
						setsvs_report(response.data[0].Data);
						setsvs_report_copy(response.data[0].Data);

						if (response.data) {
							setshow_table(false);
							setshow_Skeleton(false);
							showSuccess("Data Fetched");
							setBlocked(false);
							setloading_show(false);
						}
					});
			}
		}

		setBlocked(false);
		setloading_show(false);
	};
	// console.log(original_data);
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

	const exportCSV = (selectionOnly) => {
		dt.current.exportCSV({ selectionOnly });
	};

	const onGlobalFilterChange = (e) => {
		const value = e.target.value;
		let _filters = { ...filters };

		_filters["global"].value = value;

		setFilters(_filters);
		setGlobalFilterValue(value);
	};

	const header = (
		<>
			<div style={{ backgroundColor: "#ffffff" }}>
				<div className="flex flex-wrap gap-1 justify-content-between align-items-center">
					<div className="field">
						<span className="p-input-icon-left">
							<i className="pi pi-search" />
							<InputText
								col={20}
								value={globalFilterValue}
								onChange={onGlobalFilterChange}
								placeholder="Search Anything from Report"
							/>
						</span>
						
						{/* <Button
							size="small"
							severity="info"
							label="Error List"
							icon="pi pi-file-excel"
							rounded
							raised
							onClick={() => error_list()}
						/> */}
					</div>
					<div className="field"></div>
					<div className="field"></div>
					<div className="field">
						<span className="p-input-icon-left">
							<Button
								disabled={show_Skeleton}
								severity="info"
								label="SEM vs SCADA Report(.csv)"
								icon="pi pi-file-excel"
								text
								onClick={() => exportCSV(false)}
							/>
						</span>
					</div>
					<div className="field">
						<a
							href={
								"http://10.3.230.62:5003/letters_zip?startDate=" +
								moment(start_date).format("DD-MM-YYYY") +
								"&endDate=" +
								moment(end_date).format("DD-MM-YYYY")
							}
						>
							<b style={{ fontSize: "medium", fontStyle: "revert-layer" }}>
								Download Letters(.zip)
							</b>
							<Avatar
								icon="pi pi-download"
								style={{ backgroundColor: "red", color: "#ffffff" }}
								shape="circle"
							/>
						</a>

						<a
							href={
								"http://10.3.230.62:5003/GetSvSExcel?startDate=" +
								moment(start_date).format("DD-MM-YYYY") +
								"&endDate=" +
								moment(end_date).format("DD-MM-YYYY")
							}
						>
							<b style={{ fontSize: "medium", fontStyle: "revert-layer" }}>
								Download all Data(.xlsx)
							</b>
							<Avatar
								shape="circle"
								icon="pi pi-file-excel"
								style={{ backgroundColor: "green", color: "#ffffff" }}
							/>
						</a>

						<a
							href={
								"http://10.3.230.62:5003/GetErrorExcel?startDate=" +
								moment(start_date).format("DD-MM-YYYY") +
								"&endDate=" +
								moment(end_date).format("DD-MM-YYYY")
							}
						>
							<b style={{ fontSize: "medium", fontStyle: "revert-layer" }}>
								Error List
							</b>
							<Avatar
								icon="pi pi-ban"
								style={{ backgroundColor: "black", color: "#ffffff" }}
								shape="circle"
							/>
						</a>
					</div>
				</div>
			</div>
		</>
	);

	// const randomNum = () => Math.floor(Math.random() * (235 - 52 + 1) + 52);

	// const randomRGB = () => `rgb(${randomNum()}, ${randomNum()}, ${randomNum()})`;

	const rendergraphfarend = (e) => {
		if (selectedrows.length === 1) {
			if (invert) {
				var to_end_scada = selectedrows[0].Scada_To_End_data.map((a) => a * -1);
				var to_end_meter = selectedrows[0].Meter_To_End_data.map((a) => a * -1);
			} else {
				var to_end_scada = selectedrows[0].Scada_To_End_data;
				var to_end_meter = selectedrows[0].Meter_To_End_data;
			}

			return (
				<>
					<Button
						onClick={() => {
							setgraph_header("To End vs Far End Graph");
							settable_header("To End vs Far End Table");
							setrowgraph(true);
							setfar_end_graph(false);
							setto_end_graph(true);
							// setgraph_header("Far");
							var Far_table_val1 = [];
							var far_name = selectedrows[0].Feeder_Name.split("_");

							if (far_name.length == 4) {
								far_name =
									far_name[0] +
									"_" +
									far_name[2] +
									"_" +
									far_name[1] +
									"_" +
									far_name[3];
							} else if (far_name.length == 3) {
								far_name = far_name[0] + "_" + far_name[2] + "_" + far_name[1];
							} else {
								far_name = selectedrows[0].Feeder_Name;
							}

							Far_table_val1.push({
								Feeder_Name: "To End Data: " + selectedrows[0].Feeder_Name,
								SCADA_Key: selectedrows[0].Key_To_End,
								SEM_Key: selectedrows[0].Meter_To_End,
								SCADA_vs_SCADA: selectedrows[0].scada_avg + " %",
								SEM_vs_SEM: selectedrows[0].sem_avg + " %",
								To_End_Error: selectedrows[0].to_end_avg_val + " %",
								Far_End_Error: selectedrows[0].far_end_avg_val + " %",
							});

							Far_table_val1.push({
								Feeder_Name: "Far End Data: " + far_name,
								SCADA_Key: selectedrows[0].Key_Far_End,
								SEM_Key: selectedrows[0].Meter_Far_End,
								SCADA_vs_SCADA: selectedrows[0].scada_avg + " %",
								SEM_vs_SEM: selectedrows[0].sem_avg + " %",
								To_End_Error: selectedrows[0].to_end_avg_val + " %",
								Far_End_Error: selectedrows[0].far_end_avg_val + " %",
							});

							setFar_table_val(Far_table_val1);

							const documentStyle = getComputedStyle(document.documentElement);
							const textColor = documentStyle.getPropertyValue("--text-color");
							const textColorSecondary = documentStyle.getPropertyValue(
								"--text-color-secondary"
							);
							const surfaceBorder =
								documentStyle.getPropertyValue("--surface-border");
							const data = {
								labels: original_data.Date_Time,
								datasets: [
									{
										label:
											"SEM vs SCADA plot of " +
											selectedrows[0].Feeder_Name +
											" To End (" +
											selectedrows[0].Meter_To_End +
											" vs " +
											selectedrows[0].Key_To_End +
											")",
										data: selectedrows[0].to_end_percent,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--yellow-200"),
										tension: 0.4,
										yAxisID: "y1",
										hidden: true,
									},
									{
										label:
											"SCADA plot of " +
											selectedrows[0].Feeder_Name +
											" To End (" +
											selectedrows[0].Key_To_End +
											")",
										data: to_end_scada,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--blue-500"),
										tension: 0.4,
										yAxisID: "y",
									},

									{
										label:
											"SEM plot of " +
											selectedrows[0].Feeder_Name +
											" To End (" +
											selectedrows[0].Meter_To_End +
											")",
										data: to_end_meter,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--pink-500"),
										tension: 0.4,
										yAxisID: "y",
									},
									{
										label:
											"SEM vs SCADA plot of " +
											far_name +
											" Far End (" +
											selectedrows[0].Meter_Far_End +
											" vs " +
											selectedrows[0].Key_Far_End +
											")",
										data: selectedrows[0].far_end_percent,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--green-200"),
										tension: 0.4,
										yAxisID: "y1",
										hidden: true,
									},
									{
										label:
											"SCADA plot of " +
											far_name +
											" Far End (" +
											selectedrows[0].Key_Far_End +
											")",
										data: selectedrows[0].Scada_Far_End_data,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--blue-400"),
										tension: 0.4,
										yAxisID: "y",
									},

									{
										label:
											"SEM plot of " +
											far_name +
											" Far End (" +
											selectedrows[0].Meter_Far_End +
											")",
										data: selectedrows[0].Meter_Far_End_data,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--pink-400"),
										tension: 0.4,
										yAxisID: "y",
									},
								],
							};
							const options = {
								stacked: false,
								maintainAspectRatio: false,
								aspectRatio: 0.5,
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
										title: {
											display: true,
											text: "Date Time Block",
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
											text: "SEM & SCADA (To & Far End) Data",
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
											text: "SEM vs SCADA (To & Far End) Error %",
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

							setChartData1(data);
							setChartOptions1(options);
						}}
						rounded
						text
						severity="danger"
						label={e["far_end_avg_val"] + " %"}
					/>
				</>
			);
		} else if (selectedrows.length > 1) {
			return (
				<>
					<Button
						onClick={() => {
							setgraph_header("Far End Graph comparison");
							settable_header("Far End comparison Table");
							setrowgraph(true);
							setfar_end_graph(false);
							setto_end_graph(true);
							// setgraph_header("Far");
							var Far_table_val1 = [];

							const documentStyle = getComputedStyle(document.documentElement);
							const textColor = documentStyle.getPropertyValue("--text-color");
							const textColorSecondary = documentStyle.getPropertyValue(
								"--text-color-secondary"
							);
							const surfaceBorder =
								documentStyle.getPropertyValue("--surface-border");

							const data = {
								labels: original_data.Date_Time,
							};

							var all_datasets = [];

							{
								selectedrows.map((f) => {
									var far_name1 = f.Feeder_Name.split("_");

									if (far_name1.length == 4) {
										far_name1 =
											far_name1[0] +
											"_" +
											far_name1[2] +
											"_" +
											far_name1[1] +
											"_" +
											far_name1[3];
									} else if (far_name1.length == 3) {
										far_name1 =
											far_name1[0] + "_" + far_name1[2] + "_" + far_name1[1];
									} else {
										far_name1 = f.Feeder_Name;
									}
									Far_table_val1.push({
										Feeder_Name: "Far End: " + far_name1,
										SCADA_Key: f.Key_Far_End,
										SEM_Key: f.Meter_Far_End,
										SCADA_vs_SCADA: f.scada_avg + " %",
										SEM_vs_SEM: f.sem_avg + " %",
										To_End_Error: f.to_end_avg_val + " %",
										Far_End_Error: f.far_end_avg_val + " %",
									});

									all_datasets.push(
										{
											label:
												"SEM vs SCADA plot of " +
												far_name1 +
												" Far End (" +
												f.Meter_Far_End +
												" vs " +
												f.Key_Far_End +
												")",
											data: f.far_end_percent,
											fill: false,
											borderColor:
												documentStyle.getPropertyValue("--green-200"),
											tension: 0.4,
											yAxisID: "y1",
											hidden: true,
										},
										{
											label:
												"SCADA plot of " +
												far_name1 +
												" Far End (" +
												f.Key_Far_End +
												")",
											data: f.Scada_Far_End_data,
											fill: false,
											borderColor: documentStyle.getPropertyValue("--blue-500"),
											tension: 0.4,
											yAxisID: "y",
										},

										{
											label:
												"SEM plot of " +
												far_name1 +
												" Far End (" +
												f.Meter_Far_End +
												")",
											data: f.Meter_Far_End_data,
											fill: false,
											borderColor: documentStyle.getPropertyValue("--pink-500"),
											tension: 0.4,
											yAxisID: "y",
										}
									);
								});
							}
							data["datasets"] = all_datasets;
							setFar_table_val(Far_table_val1);

							const options = {
								stacked: false,
								maintainAspectRatio: false,
								aspectRatio: 0.5,
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
										title: {
											display: true,
											text: "Date Time Block",
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
											text: "SEM(To End) & SCADA(Far End) Data",
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
											text: "SEM(To End) vs SCADA(Far End) Error %",
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

							setChartData1(data);
							setChartOptions1(options);
						}}
						rounded
						text
						severity="danger"
						label={e["far_end_avg_val"] + " %"}
					/>
				</>
			);
		} else {
			return (
				<>
					<Button
						onClick={() => {
							setgraph_header("Far End Sem vs Scada Graph");
							settable_header("Far End Sem vs Scada Table");
							setrowgraph(true);
							setfar_end_graph(false);
							setto_end_graph(true);
							// setgraph_header("Far");
							var Far_table_val1 = [];

							var far_name2 = e.Feeder_Name.split("_");

							if (far_name2.length == 4) {
								far_name2 =
									far_name2[0] +
									"_" +
									far_name2[2] +
									"_" +
									far_name2[1] +
									"_" +
									far_name2[3];
							} else if (far_name2.length == 3) {
								far_name2 =
									far_name2[0] + "_" + far_name2[2] + "_" + far_name2[1];
							} else {
								far_name2 = e.Feeder_Name;
							}

							Far_table_val1.push({
								Feeder_Name: "Far End: " + far_name2,
								SCADA_Key: e.Key_Far_End,
								SEM_Key: e.Meter_Far_End,
								SCADA_vs_SCADA: e.scada_avg + " %",
								SEM_vs_SEM: e.sem_avg + " %",
								To_End_Error: e.to_end_avg_val + " %",
								Far_End_Error: e.far_end_avg_val + " %",
							});

							setFar_table_val(Far_table_val1);

							const documentStyle = getComputedStyle(document.documentElement);
							const textColor = documentStyle.getPropertyValue("--text-color");
							const textColorSecondary = documentStyle.getPropertyValue(
								"--text-color-secondary"
							);
							const surfaceBorder =
								documentStyle.getPropertyValue("--surface-border");
							const data = {
								labels: original_data.Date_Time,
								datasets: [
									{
										label:
											"SEM vs SCADA plot of " +
											far_name2 +
											" Far End (" +
											e.Meter_Far_End +
											" vs " +
											e.Key_Far_End +
											")",
										data: e.far_end_percent,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--green-200"),
										tension: 0.4,
										yAxisID: "y1",
									},
									{
										label:
											"SCADA plot of " +
											far_name2 +
											" Far End (" +
											e.Key_Far_End +
											")",
										data: e.Scada_Far_End_data,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--blue-500"),
										tension: 0.4,
										yAxisID: "y",
									},

									{
										label:
											"SEM plot of " +
											far_name2 +
											" Far End (" +
											e.Meter_Far_End +
											")",
										data: e.Meter_Far_End_data,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--pink-500"),
										tension: 0.4,
										yAxisID: "y",
									},
								],
							};
							const options = {
								stacked: false,
								maintainAspectRatio: false,
								aspectRatio: 0.5,
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
										title: {
											display: true,
											text: "Date Time Block",
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
											text: "SCADA(Far End) & SEM(Far End) Data",
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
											text: "SCADA(Far End) vs SEM(Far End) Error %",
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

							setChartData1(data);
							setChartOptions1(options);
						}}
						rounded
						text
						severity="danger"
						label={e["far_end_avg_val"] + " %"}
					/>
				</>
			);
		}
	};

	const rendergraphtoend = (e) => {
		if (selectedrows.length === 1) {
			if (invert) {
				var to_end_scada = selectedrows[0].Scada_To_End_data.map((a) => a * -1);
				var to_end_meter = selectedrows[0].Meter_To_End_data.map((a) => a * -1);
			} else {
				var to_end_scada = selectedrows[0].Scada_To_End_data;
				var to_end_meter = selectedrows[0].Meter_To_End_data;
			}

			return (
				<>
					<Button
						onClick={() => {
							setgraph_header("To End vs Far End Graph");
							settable_header("To End vs Far End Table");
							setrowgraph(true);
							setfar_end_graph(true);
							setto_end_graph(false);
							// setgraph_header("Far");
							var To_table_val1 = [];

							var far_name3 = selectedrows[0].Feeder_Name.split("_");

							if (far_name3.length == 4) {
								far_name3 =
									far_name3[0] +
									"_" +
									far_name3[2] +
									"_" +
									far_name3[1] +
									"_" +
									far_name3[3];
							} else if (far_name3.length == 3) {
								far_name3 =
									far_name3[0] + "_" + far_name3[2] + "_" + far_name3[1];
							} else {
								far_name3 = selectedrows[0].Feeder_Name;
							}
							// console.log(far_name3)

							To_table_val1.push({
								Feeder_Name: "To End: " + selectedrows[0].Feeder_Name,
								SCADA_Key: selectedrows[0].Key_To_End,
								SEM_Key: selectedrows[0].Meter_To_End,
								SCADA_vs_SCADA: selectedrows[0].scada_avg + " %",
								SEM_vs_SEM: selectedrows[0].sem_avg + " %",
								To_End_Error: selectedrows[0].to_end_avg_val + " %",
								Far_End_Error: selectedrows[0].far_end_avg_val + " %",
							});

							To_table_val1.push({
								Feeder_Name: "Far End: " + selectedrows[0].Feeder_Name,
								SCADA_Key: selectedrows[0].Key_To_End,
								SEM_Key: selectedrows[0].Meter_To_End,
								SCADA_vs_SCADA: selectedrows[0].scada_avg + " %",
								SEM_vs_SEM: selectedrows[0].sem_avg + " %",
								To_End_Error: selectedrows[0].to_end_avg_val + " %",
								Far_End_Error: selectedrows[0].far_end_avg_val + " %",
							});

							setTo_table_val(To_table_val1);

							const documentStyle = getComputedStyle(document.documentElement);
							const textColor = documentStyle.getPropertyValue("--text-color");
							const textColorSecondary = documentStyle.getPropertyValue(
								"--text-color-secondary"
							);
							const surfaceBorder =
								documentStyle.getPropertyValue("--surface-border");
							const data = {
								labels: original_data.Date_Time,
								datasets: [
									{
										label:
											"SEM vs SCADA plot of " +
											selectedrows[0].Feeder_Name +
											" To End (" +
											selectedrows[0].Meter_To_End +
											" vs " +
											selectedrows[0].Key_To_End +
											")",
										data: selectedrows[0].to_end_percent,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--yellow-200"),
										tension: 0.4,
										yAxisID: "y1",
										hidden: true,
									},
									{
										label:
											"SCADA plot of " +
											selectedrows[0].Feeder_Name +
											" To End (" +
											selectedrows[0].Key_To_End +
											")",
										data: to_end_scada,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--blue-500"),
										tension: 0.4,
										yAxisID: "y",
									},

									{
										label:
											"SEM plot of " +
											selectedrows[0].Feeder_Name +
											" To End (" +
											selectedrows[0].Meter_To_End +
											")",
										data: to_end_meter,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--pink-500"),
										tension: 0.4,
										yAxisID: "y",
									},
									{
										label:
											"SEM vs SCADA plot of " +
											far_name3 +
											" Far End (" +
											selectedrows[0].Meter_Far_End +
											" vs " +
											selectedrows[0].Key_Far_End +
											")",
										data: selectedrows[0].far_end_percent,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--green-200"),
										tension: 0.4,
										yAxisID: "y1",
										hidden: true,
									},
									{
										label:
											"SCADA plot of " +
											far_name3 +
											" Far End (" +
											selectedrows[0].Key_Far_End +
											")",
										data: selectedrows[0].Scada_Far_End_data,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--blue-400"),
										tension: 0.4,
										yAxisID: "y",
									},

									{
										label:
											"SEM plot of " +
											far_name3 +
											" Far End (" +
											selectedrows[0].Meter_Far_End +
											")",
										data: selectedrows[0].Meter_Far_End_data,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--pink-400"),
										tension: 0.4,
										yAxisID: "y",
									},
								],
							};
							const options = {
								stacked: false,
								maintainAspectRatio: false,
								aspectRatio: 0.5,
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
										title: {
											display: true,
											text: "Date Time Block",
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
											text: "SEM & SCADA (To & Far End) Data",
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
											text: "SEM vs SCADA (To & Far End) Error %",
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

							setChartData1(data);
							setChartOptions1(options);
						}}
						rounded
						text
						severity="danger"
						label={e["to_end_avg_val"] + " %"}
					/>
				</>
			);
		} else if (selectedrows.length > 1) {
			return (
				<>
					<Button
						onClick={() => {
							setgraph_header("To End Graph comparison");
							settable_header("To End comparison Table");
							setrowgraph(true);
							setfar_end_graph(true);
							setto_end_graph(false);
							// setgraph_header("To");
							var To_table_val1 = [];

							const documentStyle = getComputedStyle(document.documentElement);
							const textColor = documentStyle.getPropertyValue("--text-color");
							const textColorSecondary = documentStyle.getPropertyValue(
								"--text-color-secondary"
							);
							const surfaceBorder =
								documentStyle.getPropertyValue("--surface-border");

							const data = {
								labels: original_data.Date_Time,
							};

							var all_datasets = [];

							{
								selectedrows.map((g) => {
									To_table_val1.push({
										Feeder_Name: "To End: " + selectedrows[0].Feeder_Name,
										SCADA_Key: selectedrows[0].Key_To_End,
										SEM_Key: selectedrows[0].Meter_To_End,
										SCADA_vs_SCADA: selectedrows[0].scada_avg + " %",
										SEM_vs_SEM: selectedrows[0].sem_avg + " %",
										To_End_Error: selectedrows[0].to_end_avg_val + " %",
										Far_End_Error: selectedrows[0].far_end_avg_val + " %",
									});

									all_datasets.push(
										{
											label:
												"SEM vs SCADA plot of " +
												g.Feeder_Name +
												" To End (" +
												g.Meter_To_End +
												" vs " +
												g.Key_To_End +
												")",
											data: g.to_end_percent,
											fill: false,
											borderColor:
												documentStyle.getPropertyValue("--green-200"),
											tension: 0.4,
											yAxisID: "y1",
											hidden: true,
										},
										{
											label:
												"SCADA plot of " +
												g.Feeder_Name +
												" To End (" +
												g.Key_To_End +
												")",
											data: g.Scada_To_End_data,
											fill: false,
											borderColor: documentStyle.getPropertyValue("--blue-500"),
											tension: 0.4,
											yAxisID: "y",
										},

										{
											label:
												"SEM plot of " +
												g.Feeder_Name +
												" To End (" +
												g.Meter_To_End +
												")",
											data: g.Meter_To_End_data,
											fill: false,
											borderColor: documentStyle.getPropertyValue("--pink-500"),
											tension: 0.4,
											yAxisID: "y",
										}
									);
								});
							}
							setTo_table_val(To_table_val1);
							data["datasets"] = all_datasets;

							const options = {
								stacked: false,
								maintainAspectRatio: false,
								aspectRatio: 0.5,
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
										title: {
											display: true,
											text: "Date Time Block",
										},
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
										title: {
											display: true,
											text: "SEM(To End) & SCADA(Far End) Data",
										},
										ticks: {
											color: textColorSecondary,
										},
										grid: {
											color: surfaceBorder,
										},
									},
									y1: {
										type: "linear",
										display: true,
										position: "right",
										title: {
											display: true,
											text: "SEM(To End) vs SCADA(Far End) Error %",
										},
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

							setChartData1(data);
							setChartOptions1(options);
						}}
						rounded
						text
						severity="danger"
						label={e["to_end_avg_val"] + " %"}
					/>
				</>
			);
		} else {
			return (
				<>
					<Button
						onClick={() => {
							setgraph_header("To End Sem vs Scada Graph");
							settable_header("To End Sem vs Scada Table");
							setrowgraph(true);
							setfar_end_graph(true);
							setto_end_graph(false);
							// setgraph_header("To");
							var To_table_val1 = [];

							To_table_val1.push({
								Feeder_Name: "To End: " + e.Feeder_Name,
								SCADA_Key: e.Key_To_End,
								SEM_Key: e.Meter_To_End,
								SCADA_vs_SCADA: e.scada_avg + " %",
								SEM_vs_SEM: e.sem_avg + " %",
								To_End_Error: e.to_end_avg_val + " %",
								Far_End_Error: e.far_end_avg_val + " %",
							});

							setTo_table_val(To_table_val1);

							const documentStyle = getComputedStyle(document.documentElement);
							const textColor = documentStyle.getPropertyValue("--text-color");
							const textColorSecondary = documentStyle.getPropertyValue(
								"--text-color-secondary"
							);
							const surfaceBorder =
								documentStyle.getPropertyValue("--surface-border");
							const data = {
								labels: original_data.Date_Time,
								datasets: [
									{
										label:
											"SEM vs SCADA plot of " +
											e.Feeder_Name +
											" To End (" +
											e.Meter_To_End +
											" vs " +
											e.Key_To_End +
											")",
										data: e.to_end_percent,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--green-200"),
										tension: 0.4,
										yAxisID: "y1",
									},
									{
										label:
											"SCADA plot of " +
											e.Feeder_Name +
											" To End (" +
											e.Key_To_End +
											")",
										data: e.Scada_To_End_data,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--blue-500"),
										tension: 0.4,
										yAxisID: "y",
									},

									{
										label:
											"SEM plot of " +
											e.Feeder_Name +
											" To End (" +
											e.Meter_To_End +
											")",
										data: e.Meter_To_End_data,
										fill: false,
										borderColor: documentStyle.getPropertyValue("--pink-500"),
										tension: 0.4,
										yAxisID: "y",
									},
								],
							};
							const options = {
								stacked: false,
								maintainAspectRatio: false,
								aspectRatio: 0.5,
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
										title: {
											display: true,
											text: "Date Time Block",
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
											text: "SCADA(To End) & SEM(To End) Data",
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
											text: "SCADA(To End) vs SEM(To End) Error %",
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

							setChartData1(data);
							setChartOptions1(options);
						}}
						rounded
						text
						severity="danger"
						label={e["to_end_avg_val"] + " %"}
					/>
				</>
			);
		}
	};

	const rendergraphScada = (e) => {
		if (invert) {
			var far_end_scada = e.Scada_Far_End_data.map((a) => a * -1);
		} else {
			var far_end_scada = e.Scada_Far_End_data;
		}

		var rev_far_name = e.Feeder_Name.split("_");

		if (rev_far_name.length == 4) {
			rev_far_name =
				rev_far_name[0] +
				"_" +
				rev_far_name[2] +
				"_" +
				rev_far_name[1] +
				"_" +
				rev_far_name[3];
		} else if (rev_far_name.length == 3) {
			rev_far_name =
				rev_far_name[0] + "_" + rev_far_name[2] + "_" + rev_far_name[1];
		} else {
			rev_far_name = e.Feeder_Name;
		}

		return (
			<>
				<Button
					onClick={() => {
						setgraph_header("Scada To End vs Scada Far End Graph");
						settable_header("Scada To End vs Scada Far End Table");
						setrowgraph(true);
						setfar_end_graph(true);
						setto_end_graph(false);
						// setgraph_header("To");
						var To_table_val1 = [];

						To_table_val1.push({
							Feeder_Name: e.Feeder_Name,
							To_End_SCADA_Key: e.Key_To_End,
							Far_End_SCADA_Key: e.Key_Far_End,
							SCADA_vs_SCADA: e.scada_avg + " %",
							SEM_vs_SEM: e.sem_avg + " %",
							To_End_Error: e.to_end_avg_val + " %",
							Far_End_Error: e.far_end_avg_val + " %",
						});
						setTo_table_val(To_table_val1);

						const documentStyle = getComputedStyle(document.documentElement);
						const textColor = documentStyle.getPropertyValue("--text-color");
						const textColorSecondary = documentStyle.getPropertyValue(
							"--text-color-secondary"
						);
						const surfaceBorder =
							documentStyle.getPropertyValue("--surface-border");
						const data = {
							labels: original_data.Date_Time,
							datasets: [
								{
									label:
										"SCADA vs SCADA plot of " +
										e.Feeder_Name +
										" To End (" +
										e.Key_To_End +
										" vs " +
										e.Key_Far_End +
										")",
									data: e.scada_error,
									fill: false,
									borderColor: documentStyle.getPropertyValue("--green-200"),
									tension: 0.4,
									yAxisID: "y1",
								},
								{
									label:
										"SCADA To End plot of " +
										e.Feeder_Name +
										" To End (" +
										e.Key_To_End +
										")",
									data: e.Scada_To_End_data,
									fill: false,
									borderColor: documentStyle.getPropertyValue("--blue-500"),
									tension: 0.4,
									yAxisID: "y",
								},

								{
									label:
										"SCADA Far End plot of " +
										rev_far_name +
										" Far End (" +
										e.Key_Far_End +
										")",
									data: far_end_scada,
									fill: false,
									borderColor: documentStyle.getPropertyValue("--pink-500"),
									tension: 0.4,
									yAxisID: "y",
								},
							],
						};
						const options = {
							stacked: false,
							maintainAspectRatio: false,
							aspectRatio: 0.5,
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
									title: {
										display: true,
										text: "Date Time Block",
									},
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
									title: {
										display: true,
										text: "SCADA(To End) & SCADA(Far End) Data",
									},
									ticks: {
										color: textColorSecondary,
									},
									grid: {
										color: surfaceBorder,
									},
								},
								y1: {
									type: "linear",
									display: true,
									position: "right",
									title: {
										display: true,
										text: "SCADA(To End) vs SCADA(Far End) Error %",
									},
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

						setChartData1(data);
						setChartOptions1(options);
					}}
					rounded
					text
					severity="secondary"
					label={e["scada_avg"] + " %"}
				/>
			</>
		);
	};

	const rendergraphSem = (e) => {
		if (invert) {
			var far_end_sem = e.Meter_Far_End_data.map((a) => a * -1);
		} else {
			var far_end_sem = e.Meter_Far_End_data;
		}

		var rev_far_name = e.Feeder_Name.split("_");

		if (rev_far_name.length == 4) {
			rev_far_name =
				rev_far_name[0] +
				"_" +
				rev_far_name[2] +
				"_" +
				rev_far_name[1] +
				"_" +
				rev_far_name[3];
		} else if (rev_far_name.length == 3) {
			rev_far_name =
				rev_far_name[0] + "_" + rev_far_name[2] + "_" + rev_far_name[1];
		} else {
			rev_far_name = e.Feeder_Name;
		}

		return (
			<>
				<Button
					onClick={() => {
						setgraph_header("Sem To End vs Sem Far End Graph");
						settable_header("Sem To End vs Sem Far End Table");
						setrowgraph(true);
						setfar_end_graph(true);
						setto_end_graph(false);
						// setgraph_header("To");
						var To_table_val1 = [];

						To_table_val1.push({
							Feeder_Name: e.Feeder_Name,
							To_End_SEM_Key: e.Meter_To_End,
							Far_End_SEM_Key: e.Meter_Far_End,
							SCADA_vs_SCADA: e.scada_avg + " %",
							SEM_vs_SEM: e.sem_avg + " %",
							To_End_Error: e.to_end_avg_val + " %",
							Far_End_Error: e.far_end_avg_val + " %",
						});
						setTo_table_val(To_table_val1);

						const documentStyle = getComputedStyle(document.documentElement);
						const textColor = documentStyle.getPropertyValue("--text-color");
						const textColorSecondary = documentStyle.getPropertyValue(
							"--text-color-secondary"
						);
						const surfaceBorder =
							documentStyle.getPropertyValue("--surface-border");
						const data = {
							labels: original_data.Date_Time,
							datasets: [
								{
									label:
										"SEM vs SEM plot of " +
										e.Feeder_Name +
										" To End (" +
										e.Meter_To_End +
										" vs " +
										e.Key_To_End +
										")",
									data: e.sem_error,
									fill: false,
									borderColor: documentStyle.getPropertyValue("--green-200"),
									tension: 0.4,
									yAxisID: "y1",
								},
								{
									label:
										"SEM To End plot of " +
										e.Feeder_Name +
										" To End (" +
										e.Meter_To_End +
										")",
									data: e.Meter_To_End_data,
									fill: false,
									borderColor: documentStyle.getPropertyValue("--blue-500"),
									tension: 0.4,
									yAxisID: "y",
								},

								{
									label:
										"SEM Far End plot of " +
										rev_far_name +
										" Far End (" +
										e.Meter_Far_End +
										")",
									data: far_end_sem,
									fill: false,
									borderColor: documentStyle.getPropertyValue("--pink-500"),
									tension: 0.4,
									yAxisID: "y",
								},
							],
						};
						const options = {
							stacked: false,
							maintainAspectRatio: false,
							aspectRatio: 0.5,
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
									title: {
										display: true,
										text: "Date Time Block",
									},
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
									title: {
										display: true,
										text: "SEM(To End) & SEM(Far End) Data",
									},
									ticks: {
										color: textColorSecondary,
									},
									grid: {
										color: surfaceBorder,
									},
								},
								y1: {
									type: "linear",
									display: true,
									position: "right",
									title: {
										display: true,
										text: "SEM(To End) vs SEM(Far End) Error %",
									},
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

						setChartData1(data);
						setChartOptions1(options);
					}}
					rounded
					text
					severity="secondary"
					label={e["sem_avg"] + " %"}
				/>
			</>
		);
	};

	const avgFilterTemplate = (options) => {
		return (
			<InputNumber
				value={options.value}
				onChange={(e) => options.filterCallback(e.value, options.index)}
			/>
		);
	};

	const saveAsExcelFile = (buffer, fileName) => {
		import("file-saver").then((module) => {
			if (module && module.default) {
				let EXCEL_TYPE =
					"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8";
				let EXCEL_EXTENSION = ".xlsx";
				const data = new Blob([buffer], {
					type: EXCEL_TYPE,
				});

				module.default.saveAs(data, fileName + EXCEL_EXTENSION);
			}
		});
	};

	const handleExport = () => {
		if (chartData1) {
			var excel_data = [];
			for (var i = 0; i < chartData1.labels.length; i++) {
				var t1 = {
					Date: chartData1.labels[i],
				};

				for (var j = 0; j < chartData1.datasets.length; j++) {
					t1[chartData1.datasets[j].label] = chartData1.datasets[j].data[i];
				}

				excel_data.push(t1);
			}
		}
		import("xlsx").then((xlsx) => {
			const worksheet = xlsx.utils.json_to_sheet(excel_data);
			const workbook = { Sheets: { data: worksheet }, SheetNames: ["data"] };
			const excelBuffer = xlsx.write(workbook, {
				bookType: "xlsx",
				type: "array",
			});

			saveAsExcelFile(excelBuffer, chartData1.datasets[0].label);
		});
	};

	const cellClassName = (data) =>
		data
			? String(data).includes("No Key:")
				? "p-max-min"
				: error_names.indexOf(data) > -1
				? "p-error"
				: ""
			: "";



	return (
		<>
			<div hidden={!loading_show}>
				<div className="loader">
					<div className="spinner"></div>
				</div>
			</div>

			<BlockUI blocked={blocked} fullScreen />
			<div className="card flex justify-content-center">
				<Dialog
					maximized
					maximizable
					header={graph_header}
					visible={rowgraph}
					style={{ width: "80vw" }}
					onHide={() => setrowgraph(false)}
				>
					<div align="left" style={{ fontWeight: "bold" }}>
						Invert To End Graph
						<InputSwitch
							tooltip="Click to Invert"
							checked={invert}
							onChange={(e) => setinvert(e.value)}
						/>
					</div>
					<div align="right">
						<Button
							icon="pi pi-file-excel"
							severity="success"
							raised
							rounded
							onClick={handleExport}
						>
							Export to Excel
						</Button>
					</div>

					<div className="card">
						<Chart type="line" data={chartData1} options={chartOptions1} />
					</div>

					<div hidden={far_end_graph}>
						<h4 align="center">{table_header}</h4>
						<DataTable size="small" showGridlines value={Far_table_val}>
							<Column
								field="Feeder_Name"
								header="FEEDER Name"
								style={{ color: "green" }}
							></Column>
							<Column
								align={"center"}
								field="SCADA_Key"
								header="SCADA Key"
							></Column>
							<Column
								align={"center"}
								field="SEM_Key"
								header="SEM Key"
							></Column>
							<Column
								align={"center"}
								field="SCADA_vs_SCADA"
								header="SCADA vs SCADA"
								style={{ color: "blue" }}
							></Column>
							<Column
								align={"center"}
								field="SEM_vs_SEM"
								header="SEM vs SEM"
								style={{ color: "blue" }}
							></Column>
							<Column
								align={"center"}
								field="To_End_Error"
								header="To End Error"
								style={{ color: "red" }}
							></Column>
							<Column
								align={"center"}
								field="Far_End_Error"
								header="Far End Error"
								style={{ color: "red" }}
							></Column>
						</DataTable>
					</div>

					<div hidden={to_end_graph}>
						<h4 align="center">{table_header}</h4>

						{To_table_val ? (
							To_table_val[0]["SCADA_Key"] ? (
								<DataTable size="small" showGridlines value={To_table_val}>
									<Column
										field="Feeder_Name"
										header="FEEDER Name"
										style={{ color: "green" }}
									></Column>
									<Column
										align={"center"}
										field="SCADA_Key"
										header="SCADA Key"
									></Column>
									<Column
										align={"center"}
										field="SEM_Key"
										header="SEM Key"
									></Column>
									<Column
										align={"center"}
										field="SCADA_vs_SCADA"
										header="SCADA vs SCADA"
										style={{ color: "blue" }}
									></Column>
									<Column
										align={"center"}
										field="SEM_vs_SEM"
										header="SEM vs SEM"
										style={{ color: "blue" }}
									></Column>
									<Column
										align={"center"}
										field="To_End_Error"
										header="To End Error"
										style={{ color: "red" }}
									></Column>
									<Column
										align={"center"}
										field="Far_End_Error"
										header="Far End Error"
										style={{ color: "red" }}
									></Column>
								</DataTable>
							) : To_table_val[0]["To_End_SCADA_Key"] ? (
								<DataTable size="small" showGridlines value={To_table_val}>
									<Column
										field="Feeder_Name"
										header="FEEDER Name"
										style={{ color: "green" }}
									></Column>
									<Column
										align={"center"}
										field="To_End_SCADA_Key"
										header="To End SCADA Key"
									></Column>
									<Column
										align={"center"}
										field="Far_End_SCADA_Key"
										header="Far End SCADA Key"
									></Column>
									<Column
										align={"center"}
										field="SCADA_vs_SCADA"
										header="SCADA vs SCADA"
										style={{ color: "blue" }}
									></Column>
									<Column
										align={"center"}
										field="SEM_vs_SEM"
										header="SEM vs SEM"
										style={{ color: "blue" }}
									></Column>
									<Column
										align={"center"}
										field="To_End_Error"
										header="To End Error"
										style={{ color: "red" }}
									></Column>
									<Column
										align={"center"}
										field="Far_End_Error"
										header="Far End Error"
										style={{ color: "red" }}
									></Column>
								</DataTable>
							) : (
								<DataTable size="small" showGridlines value={To_table_val}>
									<Column
										field="Feeder_Name"
										header="FEEDER Name"
										style={{ color: "green" }}
									></Column>
									<Column
										align={"center"}
										field="To_End_SEM_Key"
										header="To End SEM Key"
									></Column>
									<Column
										align={"center"}
										field="Far_End_SEM_Key"
										header="Far End SEM Key"
									></Column>
									<Column
										align={"center"}
										field="SCADA_vs_SCADA"
										header="SCADA vs SCADA"
										style={{ color: "blue" }}
									></Column>
									<Column
										align={"center"}
										field="SEM_vs_SEM"
										header="SEM vs SEM"
										style={{ color: "blue" }}
									></Column>
									<Column
										align={"center"}
										field="To_End_Error"
										header="To End Error"
										style={{ color: "red" }}
									></Column>
									<Column
										align={"center"}
										field="Far_End_Error"
										header="Far End Error"
										style={{ color: "red" }}
									></Column>
								</DataTable>
							)
						) : (
							""
						)}
					</div>
				</Dialog>
			</div>
			<div className="card flex justify-content-center">
				<Toast ref={toast} />
			</div>

			<Divider align="left">
				<span
					className="p-tag"
					style={{ backgroundColor: "#000000", fontSize: "large" }}
				>
					<Avatar
						icon="pi pi-file-word"
						style={{ backgroundColor: "#000000", color: "#ffffff" }}
						shape="square"
					/>
					SEM vs SCADA Tab
				</span>
			</Divider>
			<div className="flex flex-wrap gap-1 justify-content-between align-items-center">
				<div className="field"> </div>
				<div className="field">
					<span className="p-float-label">
						Date Range:
						{/* <Calendar
								showIcon
								placeholder="Start Date"
								dateFormat="dd-mm-yy"
								value={start_date}
								onChange={(e) => {
									setStart_Date(e.value);
								}}
								monthNavigator
								yearNavigator
								yearRange="2010:2025"
								showButtonBar
							></Calendar> */}
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
				{/* <div className="field">
						<span className="p-float-label">
							<h4>To:</h4>

							<Calendar
								showIcon
								placeholder="End Date"
								dateFormat="dd-mm-yy"
								value={end_date}
								onChange={(e) => {
									setEnd_Date(e.value);
								}}
								monthNavigator
								yearNavigator
								yearRange="2010:2025"
								showButtonBar
							></Calendar>
						</span>
					</div> */}
				<div className="field">
					<span className="p-float-label">
						Offset Value:
						<InputNumber
							size={5}
							max={1440}
							step={1}
							value={offset}
							onValueChange={(e) => setoffset(e.value)}
							suffix=" MW"
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
					<span className="p-float-label" style={{ marginTop: "10%" }}>
						<Button
							raised
							rounded
							label="Generate Report"
							className="p-button-success"
							style={{
								width: "auto",
								float: "center",
							}}
							onClick={() => {
								getSEMvsSCADAreport();
								setBlocked(true);
								setloading_show(true);
							}}
						></Button>
					</span>
				</div>
				<div className="field"> </div>
			</div>

			<div hidden={show_table}>
				<Divider align="center">
					<span
						className="p-tag"
						style={{ backgroundColor: "#dc2626", fontSize: "large" }}
					>
						Selections
					</span>
				</Divider>

				<div className="flex flex-wrap gap-1 justify-content-between align-items-center">
					<div className="field"></div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom1"
							name="pizza"
							value="All"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "All"}
						/>
						<label htmlFor="FeederFrom1" className="ml-2">
							All
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom2"
							name="pizza"
							value="BH"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "BH"}
						/>
						<label htmlFor="FeederFrom2" className="ml-2">
							Bihar
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom3"
							name="pizza"
							value="DV"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "DV"}
						/>
						<label htmlFor="FeederFrom3" className="ml-2">
							DVC
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom4"
							name="pizza"
							value="GR"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "GR"}
						/>
						<label htmlFor="FeederFrom4" className="ml-2">
							Odisha
						</label>
					</div>

					<div className="field">
						<RadioButton
							inputId="FeederFrom5"
							name="pizza"
							value="JH"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "JH"}
						/>
						<label htmlFor="FeederFrom5" className="ml-2">
							Jharkhand
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom6"
							name="pizza"
							value="PG_ER1"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "PG_ER1"}
						/>
						<label htmlFor="FeederFrom6" className="ml-2">
							PG ER1
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom7"
							name="pizza"
							value="PG_ER2"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "PG_ER2"}
						/>
						<label htmlFor="FeederFrom7" className="ml-2">
							PG ER2
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom8"
							name="pizza"
							value="WB"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "WB"}
						/>
						<label htmlFor="FeederFrom8" className="ml-2">
							West Bengal
						</label>
					</div>

					<div className="field">
						<RadioButton
							inputId="FeederFrom9"
							name="pizza"
							value="SI"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "SI"}
						/>
						<label htmlFor="FeederFrom9" className="ml-2">
							Sikkim
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom10"
							name="pizza"
							value="PG_odisha_project"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "PG_odisha_project"}
						/>
						<label htmlFor="FeederFrom10" className="ml-2">
							PG Odisha Project
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom11"
							name="pizza"
							value="NTPC_ODISHA"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "NTPC_ODISHA"}
						/>
						<label htmlFor="FeederFrom11" className="ml-2">
							NTPC ODISHA
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom12"
							name="pizza"
							value="NTPC_ER_1"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "NTPC_ER_1"}
						/>
						<label htmlFor="FeederFrom12" className="ml-2">
							NTPC ER 1
						</label>
					</div>
					<div className="field">
						<RadioButton
							inputId="FeederFrom13"
							name="pizza"
							value="MIS_CALC_TO"
							onChange={(e) => setFeederFrom(e.value)}
							checked={FeederFrom === "MIS_CALC_TO"}
						/>
						<label htmlFor="FeederFrom13" className="ml-2">
							MIS CALC TO
						</label>
					</div>
					<div className="field"></div>
				</div>
			</div>

			<div className="card" hidden={!show_Skeleton}>
				<DataTable
					header={header}
					value={items}
					className="p-datatable-striped"
					reorderableColumns
					stripedRows
					size="small"
					sortField="To End Average %"
					sortOrder={-1}
					showGridlines
				>
					<Column
						field="Feeder Name"
						header="Feeder Name"
						style={{ width: "8%" }}
						sortable
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					{/* <Column
						field="Feeder Hindi"
						header="Feeder Hindi"
						style={{ width: "8%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column> */}
					<Column
						field="Key To End"
						header="Key To End"
						style={{ width: "7%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="Key Far End"
						header="Key Far End"
						style={{ width: "7%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="Meter To End"
						header="Meter To End"
						style={{ width: "8%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="Meter Far End"
						header="Meter Far End"
						style={{ width: "8%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="Feeder From"
						header="Feeder From"
						style={{ width: "7%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="To Feeder"
						header="To Feeder"
						style={{ width: "6%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="Scada vs Scada %"
						header="Scada vs Scada %"
						style={{ width: "7.5%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="Sem vs Sem %"
						header="Sem vs Sem %"
						style={{ width: "7.5%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="To End Average %"
						header="To End Average %"
						style={{ width: "9%" }}
						sortable
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					{/* <Column
						field="Far End Max %"
						header="Far End Max %"
						style={{ width: "8%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
					<Column
						field="Far End Min %"
						header="Far End Min %"
						style={{ width: "8%" }}
						body={bodyTemplate}
						headerClassName="p-head"
					></Column> */}
					<Column
						field="Far End Average %"
						header="Far End Average %"
						style={{ width: "8%" }}
						sortable
						body={bodyTemplate}
						headerClassName="p-head"
					></Column>
				</DataTable>
			</div>
			<div
				className="card"
				hidden={show_table}
				style={{
					width: "auto",
					whitespace: "nowrap",
				}}
			>
				{/* <Tooltip target=".export-buttons>button" position="bottom" /> */}
				{/* <div className="flex justify-content-center align-items-center mb-4 gap-2">
					<InputSwitch
						inputId="input-rowclick"
						checked={rowClick}
						onChange={(e) => setrowClick(e.value)}
					/>
					<label htmlFor="input-rowclick">Row Click</label>
				</div> */}
				<DataTable
				scrollHeight="830px"
					filters={filters}
					globalFilterFields={[
						"Feeder_Name",
						"Key_To_End",
						"Key_Far_End",
						"Meter_To_End",
						"Meter_Far_End",
						"Feeder_From",
						"To_Feeder",
					]}
					header={header}
					ref={dt}
					paginator
					rows={10}
					rowsPerPageOptions={[10, 25, 50, svs_report.length]}
					tableStyle={{ minWidth: "50rem" }}
					paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
					currentPageReportTemplate="Showing {first} to {last} of Total: {totalRecords} Tie-Lines"
					scrollable					
					className="mt-4"
					removableSort
					value={svs_report}
					showGridlines
					reorderableColumns
					rowHover
					size="small"
					sortField="to_end_avg_val"
					sortOrder={-1}
					cellClassName={cellClassName}
					// sortMode="multiple"
					selectionMode="checkbox"
					selection={selectedrows}
					onSelectionChange={(e) => {
						setselectedrows(e.value);
					}}
					dataKey="Feeder_Name"
				>
					<Column
						selectionMode="multiple"
						headerStyle={{ width: "3rem" }}
					></Column>
					<Column
						bodyClassName="Name"
						style={{
							maxWidth: "16rem",
							minWidth: "16rem",

							wordBreak: "break-word",
						}}
						field="Feeder_Name"
						header="Feeder Name"
						sortable
						headerClassName="p-head"
						frozen
					></Column>
					{/* <Column
						style={{
							maxWidth: "14rem",
							minWidth: "12rem",
							wordBreak: "break-word",
						}}
						field="Feeder_Hindi"
						header="Feeder Hindi"
						headerClassName="p-head"
					></Column> */}
					<Column
						style={{
							minWidth: "6rem",
							maxWidth: "6rem",
							wordBreak: "break-word",
						}}
						field="Key_To_End"
						header="Key To End"
						headerClassName="p-head"
					></Column>
					<Column
						style={{
							maxWidth: "6rem",
							minWidth: "6rem",
							wordBreak: "break-word",
						}}
						field="Key_Far_End"
						header="Key Far End"
						headerClassName="p-head"
					></Column>

					<Column
						style={{
							maxWidth: "6rem",
							minWidth: "5rem",
							wordBreak: "break-word",
						}}
						field="Meter_To_End"
						header="Meter To End"
						headerClassName="p-head"
					></Column>

					<Column
						style={{
							maxWidth: "6rem",
							minWidth: "6rem",
							wordBreak: "break-word",
						}}
						field="Meter_Far_End"
						header="Meter Far End"
						headerClassName="p-head"
					></Column>

					<Column
						style={{
							maxWidth: "6rem",
							minWidth: "6rem",
							wordBreak: "break-word",
						}}
						field="Feeder_From"
						header="Feeder From"
						sortable
						headerClassName="p-head"
					></Column>
					<Column
						style={{
							maxWidth: "6rem",
							minWidth: "6rem",
							wordBreak: "break-word",
						}}
						field="To_Feeder"
						header="To Feeder"
						sortable
						headerClassName="p-head"
					></Column>

					{/* <Column
						bodyClassName="otherPercent"
						alignHeader="center"
						align={"center"}
						style={{
							maxWidth: "4rem",
							minWidth: "4rem",
							wordBreak: "break-word",
						}}
						field="to_end_max_val"
						header="To Max %"
						headerClassName="p-head"
					></Column>
					<Column
						bodyClassName="otherPercent"
						alignHeader="center"
						align={"center"}
						style={{
							maxWidth: "4rem",
							minWidth: "4rem",
							wordBreak: "break-word",
						}}
						field="to_end_min_val"
						header="To Min %"
						headerClassName="p-head"
					></Column> */}

					<Column
					dataType="numeric"
						filterElement={avgFilterTemplate}
						filter
						filterField="scada_avg"
						alignHeader="center"
						align={"center"}
						style={{
							maxWidth: "8rem",
							minWidth: "8rem",
							wordBreak: "break-word",
						}}
						field="scada_avg"
						header="Scada vs Scada %"
						headerClassName="p-head"
						body={rendergraphScada}
						sortable
					></Column>
					<Column
					dataType="numeric"
						filterElement={avgFilterTemplate}
						filter
						filterField="sem_avg"
						alignHeader="center"
						align={"center"}
						style={{
							maxWidth: "7rem",
							minWidth: "7rem",
							wordBreak: "break-word",
						}}
						field="sem_avg"
						header="Sem vs Sem %"
						headerClassName="p-head"
						body={rendergraphSem}
						sortable
					></Column>

					<Column
						dataType="numeric"
						alignHeader="center"
						align={"center"}
						style={{
							maxWidth: "6rem",
							minWidth: "6rem",
							wordBreak: "break-word",
						}}
						field="to_end_avg_val"
						header="To %"
						filter
						filterField="to_end_avg_val"
						filterElement={avgFilterTemplate}
						sortable
						body={rendergraphtoend}
						headerClassName="p-head"
					></Column>

					{/* <Column
						bodyClassName="otherPercent"
						alignHeader="center"
						align={"center"}
						style={{
							maxWidth: "4rem",
							minWidth: "4rem",
							wordBreak: "break-word",
						}}
						field="far_end_max_val"
						header="Far Max %"
						headerClassName="p-head"
					></Column>
					<Column
						bodyClassName="otherPercent"
						alignHeader="center"
						align={"center"}
						style={{
							maxWidth: "4rem",
							minWidth: "4rem",
							wordBreak: "break-word",
						}}
						field="far_end_min_val"
						header="Far Min %"
						headerClassName="p-head"
					></Column> */}

					<Column
						dataType="numeric"
						exportable
						alignHeader="center"
						align={"center"}
						style={{
							maxWidth: "6rem",
							minWidth: "6rem",
							wordBreak: "break-word",
						}}
						field="far_end_avg_val"
						header="Far%"
						filter
						filterField="far_end_avg_val"
						sortable
						body={rendergraphfarend}
						filterElement={avgFilterTemplate}
						headerClassName="p-head"
					></Column>
				</DataTable>
			</div>
		</>
	);
}
export default SemVsScada;
