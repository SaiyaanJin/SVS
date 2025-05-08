import React, { useState, useEffect, useRef } from "react";
// import { classNames } from "primereact/utils";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Avatar } from "primereact/avatar";
import { Toast } from "primereact/toast";
import { Button } from "primereact/button";
import axios from "axios";
import { Divider } from "primereact/divider";
import { Dialog } from "primereact/dialog";
import { InputText } from "primereact/inputtext";
// import { Tag } from "primereact/tag";
import {jwtDecode } from "jwt-decode";
import { useLocation } from "react-router-dom";
import { Fieldset } from "primereact/fieldset";
import { ConfirmDialog } from "primereact/confirmdialog";
import { FilterMatchMode, FilterOperator } from "primereact/api";
import { ConfirmPopup } from "primereact/confirmpopup";
import "../cssfiles/Animation.css";
import "../cssfiles/PasswordDemo.css";
import "primeflex/primeflex.css";
import "primereact/resources/themes/lara-light-indigo/theme.css"; //theme
import "primereact/resources/primereact.min.css"; //core css
import "primeicons/primeicons.css"; //icons
import "../cssfiles/ButtonDemo.css";

function Mapping(params) {
	const search = useLocation().search;
	const id = new URLSearchParams(search).get("token");
	const [page_hide, setpage_hide] = useState(true);
	params.var6(page_hide);
	const [User_id, setUser_id] = useState();
	const [Person_Name, setPerson_Name] = useState();
	const [Department, setDepartment] = useState();
	const [isAdmin, setisAdmin] = useState(false);

	const [globalFilterValue, setGlobalFilterValue] = useState("");

	const [filters, setFilters] = useState({
		global: { value: null, matchMode: FilterMatchMode.CONTAINS },
		Feeder_Name: {
			operator: FilterOperator.AND,
			constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
		},
		Feeder_Hindi: {
			operator: FilterOperator.AND,
			constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
		},
		Feeder_From: {
			operator: FilterOperator.AND,
			constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
		},
		Key_Far_End: {
			operator: FilterOperator.AND,
			constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
		},
		Key_To_End: {
			operator: FilterOperator.AND,
			constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
		},
		Meter_Far_End: {
			operator: FilterOperator.AND,
			constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
		},
		Meter_To_End: {
			operator: FilterOperator.AND,
			constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
		},
		To_Feeder: {
			operator: FilterOperator.AND,
			constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
		},
	});

	const [popupvisible, setpopupvisible] = useState(false);
	const buttonEl = useRef(null);

	const [api_mapping_data, setapi_mapping_data] = useState([]);
	const [mapping_data_copy, setmapping_data_copy] = useState([]);
	// const [edited_row_data_e, setedited_row_data_e] = useState();
	const [edited_row_data, setedited_row_data] = useState();
	const [editDialog, seteditDialog] = useState(false);
	const [deleted_row_data, setdeleted_row_data] = useState();
	const [deleteDailog, setdeleteDailog] = useState(false);

	const [new_element_Dailog, setnew_element_Dailog] = useState(false);

	const [submitted, setSubmitted] = useState(false);
	const toast = useRef(null);
	const dt = useRef(null);

	const [Feeder_From_input, setFeeder_From_input] = useState();
	const [Feeder_Hindi_input, setFeeder_Hindi_input] = useState();
	const [Feeder_Name_input, setFeeder_Name_input] = useState();
	const [Key_Far_End_input, setKey_Far_End_input] = useState();
	const [Key_To_End_input, setKey_To_End_input] = useState();
	const [Meter_Far_End_input, setMeter_Far_End_input] = useState();
	const [Meter_To_End_input, setMeter_To_End_input] = useState();
	const [To_Feeder_input, setTo_Feeder_input] = useState();

	useEffect(() => {
		if (id) {
			axios
				.get("https://sso.erldc.in:5000/verify", {
					headers: { Token: id },
				})
				.then((response) => {
					if (response.data === "User has logout") {
						alert("User Logged-out, Please login via SSO again");
						window.location = "https://sso.erldc.in:3000";
						setpage_hide(true);
					} else if (response.data === "Bad Token") {
						alert("Unauthorised Access, Please login via SSO again");
						window.location = "https://sso.erldc.in:3000";
						setpage_hide(true);
					} else {
						var decoded = jwtDecode(response.data["Final_Token"], "it@posoco");

						if (!decoded["Login"] && decoded["Reason"] === "Session Expired") {
							alert("Session Expired, Please Login Again via SSO");

							axios
								.post("https://sso.erldc.in:5000/1ogout", {
									headers: { token: id },
								})
								.then((response) => {
									window.location = "https://sso.erldc.in:3000";
								})
								.catch((error) => {});
							window.location = "https://sso.erldc.in:3000";
						} else {
							setUser_id(decoded["User"]);
							setpage_hide(!decoded["Login"]);
							setPerson_Name(decoded["Person_Name"]);

							if (
								decoded["Department"] === "IT-TS" ||
								decoded["Department"] === "IT"
							) {
								setDepartment("Information Technology (IT)");
							}
							if (
								decoded["Department"] === "MO" ||
								decoded["Department"] === "MO-I" ||
								decoded["Department"] === "MO-II" ||
								decoded["Department"] === "MO-III" ||
								decoded["Department"] === "MO-IV"
							) {
								setDepartment("Market Operation (MO)");
							}
							if (
								decoded["Department"] === "MIS" ||
								decoded["Department"] === "SS" ||
								decoded["Department"] === "CR" ||
								decoded["Department"] === "SO"
							) {
								setDepartment("System Operation (SO)");
							}

							if (decoded["Department"] === "SCADA") {
								setDepartment("SCADA");
								axios
									.post("/Mapping_Table", {})
									.then((response) => {
										// console.log(response.data);
										setapi_mapping_data(response.data);
										setmapping_data_copy(response.data);
									})
									.catch((error) => {});
							}
							if (decoded["Department"] === "CS") {
								setDepartment("Contracts & Services (CS)");
							}
							if (decoded["Department"] === "TS") {
								setDepartment("Technical Services (TS)");
							}

							if (decoded["Department"] === "HR") {
								setDepartment("Human Resource (HR)");
							}
							if (decoded["Department"] === "COMMUNICATION") {
								setDepartment("Communication");
							}
							if (decoded["Department"] === "F&A") {
								setDepartment("Finance & Accounts (F&A)");
							}
							if (decoded["Department"] === "CR") {
								setDepartment("Control Room (CR)");
							}

							if (
								(decoded["User"] === "00162" &&
									decoded["Person_Name"] === "Sanjay Kumar") ||
								decoded["User"] === "60004"
							) {
								setisAdmin(true);
								axios
									.post("/Mapping_Table", {})
									.then((response) => {
										// console.log(response.data);
										setapi_mapping_data(response.data);
										setmapping_data_copy(response.data);
									})
									.catch((error) => {});
							} else {
								setisAdmin(false);
							}
						}
					}
				})
				.catch((error) => {});
		} else {
			setpage_hide(true);
			params.var2("Invalid_Token");
		}
	}, [User_id, page_hide, Person_Name, Department]);

	const onGlobalFilterChange = (e) => {
		const value = e.target.value;
		let _filters = { ...filters };

		_filters["global"].value = value;

		setFilters(_filters);
		setGlobalFilterValue(value);
	};

	const onRowEditComplete = (e) => {
		if (
			e.data.Feeder_Name === e.newData.Feeder_Name &&
			e.data.Feeder_Hindi === e.newData.Feeder_Hindi &&
			e.data.Key_To_End === e.newData.Key_To_End &&
			e.data.Key_Far_End === e.newData.Key_Far_End &&
			e.data.Meter_To_End === e.newData.Meter_To_End &&
			e.data.Meter_Far_End === e.newData.Meter_Far_End &&
			e.data.Feeder_From === e.newData.Feeder_From &&
			e.data.To_Feeder === e.newData.To_Feeder
		) {
			alert("No any changes detected, Noting updated");
		} else {
			setedited_row_data(e.newData);
			// setedited_row_data_e(e);
			seteditDialog(true);
		}
	};

	const textEditor = (options) => {
		var size = 8;
		if (options.field === "Feeder_Name") {
			size = 31;
		} else if (options.field === "Feeder_Hindi") {
			size = 28;
		} else {
			if (options.field === "Feeder_From" || options.field === "To_Feeder") {
				size = 10;
			} else {
				size = 6;
			}
		}
		return (
			<InputText
				size={size}
				type="text"
				value={options.value}
				onChange={(e) => options.editorCallback(e.target.value)}
			/>
		);
	};

	const accept = () => {
		if (edited_row_data) {
			axios
				.post(
					"/Mapping_Table_Update?by=" +
						Person_Name +
						" " +
						User_id,
					edited_row_data
				)
				.then((response) => {
					if (response.data === "Updated") {
						axios
							.post("/Mapping_Table", {})
							.then((response) => {
								setapi_mapping_data(response.data);
								setmapping_data_copy(response.data);
								toast.current.show({
									severity: "info",
									summary: "Updated",
									detail: "You have Updated",
									life: 3000,
								});
							})
							.catch((error) => {});
					} else {
						setmapping_data_copy(api_mapping_data);
						toast.current.show({
							severity: "error",
							summary: "Duplicate",
							detail: "Updation Failed",
							life: 3000,
						});
					}
				})
				.catch((error) => {});
		}
		seteditDialog(false);
	};

	const reject = () => {
		setmapping_data_copy(api_mapping_data);
		toast.current.show({
			severity: "warn",
			summary: "Rejected",
			detail: "You have rejected",
			life: 3000,
		});
		seteditDialog(false);
	};

	const accept1 = () => {
		if (deleted_row_data) {
			axios
				.post(
					"/Mapping_Table_Delete?by=" +
						Person_Name +
						" " +
						User_id,
					deleted_row_data
				)
				.then((response) => {
					if (response.data === "Deleted") {
						// var index = api_mapping_data.indexOf(deleted_row_data);

						// mapping_data_copy.splice(index, 1);

						axios
							.post("/Mapping_Table", {})
							.then((response) => {
								setapi_mapping_data(response.data);
								setmapping_data_copy(response.data);

								toast.current.show({
									severity: "success",
									summary: "Updated",
									detail: "You have Deleted",
									life: 3000,
								});
							})
							.catch((error) => {});
					} else {
						toast.current.show({
							severity: "error",
							summary: "Failed",
							detail: "Deletion Failed",
							life: 3000,
						});
					}
				})
				.catch((error) => {});
		}
		setdeleteDailog(false);
	};

	const reject1 = () => {
		setmapping_data_copy(api_mapping_data);
		toast.current.show({
			severity: "warn",
			summary: "Rejected",
			detail: "You have rejected",
			life: 3000,
		});
		setdeleteDailog(false);
	};

	const saveaccept = () => {
		Save_Tie_line("Some Empty");
		toast.current.show({
			severity: "info",
			summary: "Confirmed",
			detail: "You have accepted",
			life: 3000,
		});
	};

	const savereject = () => {
		toast.current.show({
			severity: "warn",
			summary: "Rejected",
			detail: "You have rejected",
			life: 3000,
		});
	};

	const openNew = () => {
		setSubmitted(false);
		setnew_element_Dailog(true);

		setFeeder_From_input();
		setFeeder_Hindi_input();
		setFeeder_Name_input();
		setKey_Far_End_input();
		setKey_To_End_input();
		setMeter_Far_End_input();
		setMeter_To_End_input();
		setTo_Feeder_input();
	};

	const hideDialog = () => {
		setSubmitted(false);
		setnew_element_Dailog(false);
		setFeeder_From_input();
		setFeeder_Hindi_input();
		setFeeder_Name_input();
		setKey_Far_End_input();
		setKey_To_End_input();
		setMeter_Far_End_input();
		setMeter_To_End_input();
		setTo_Feeder_input();
	};

	const Save_Tie_line = (response) => {
		var data_to_send = {
			Feeder_Name: Feeder_Name_input,
			Feeder_Hindi: Feeder_Hindi_input,
		};

		if (response === "All OK") {
			data_to_send["Key_To_End"] = String(Key_To_End_input);
			data_to_send["Key_Far_End"] = String(Key_Far_End_input);
			data_to_send["Meter_To_End"] = Meter_To_End_input;
			data_to_send["Meter_Far_End"] = Meter_Far_End_input;
			data_to_send["Feeder_From"] = Feeder_From_input;
			data_to_send["To_Feeder"] = To_Feeder_input;
			// data_to_send = {
			// 	Feeder_Name: Feeder_Name_input,
			//  Feeder_Hindi: Feeder_Hindi_input,
			// 	Key_To_End: String(Key_To_End_input),
			// 	Key_Far_End: String(Key_Far_End_input),
			// 	Meter_To_End: Meter_To_End_input,
			// 	Meter_Far_End: Meter_Far_End_input,
			// 	Feeder_From: Feeder_From_input,
			// 	To_Feeder: To_Feeder_input,
			// };
		} else if (response === "Some Empty") {
			if (!Key_To_End_input) {
				data_to_send["Key_To_End"] =
					"No Key:" + String(mapping_data_copy.length + 1);
			}
			if (!Key_Far_End_input) {
				data_to_send["Key_Far_End"] =
					"No Key:" + String(mapping_data_copy.length + 1);
			}
			if (!Meter_To_End_input) {
				data_to_send["Meter_To_End"] =
					"No Key:" + String(mapping_data_copy.length + 1);
			}
			if (!Meter_Far_End_input) {
				data_to_send["Meter_Far_End"] =
					"No Key:" + String(mapping_data_copy.length + 1);
			}
			if (!Feeder_From_input) {
				data_to_send["Feeder_From"] =
					"No Key:" + String(mapping_data_copy.length + 1);
			}
			if (!To_Feeder_input) {
				data_to_send["To_Feeder"] =
					"No Key:" + String(mapping_data_copy.length + 1);
			}
		}
		if (data_to_send.length !== 0) {
			axios
				.post(
					"/Mapping_Table_Add?by=" +
						Person_Name +
						" " +
						User_id,
					data_to_send
				)
				.then((response) => {
					if ((response.data = "Inserted")) {
						axios
							.post("/Mapping_Table", {})
							.then((response) => {
								setapi_mapping_data(response.data);
								setmapping_data_copy(response.data);
								hideDialog();
								toast.current.show({
									severity: "info",
									summary: "Added",
									detail: "Tie Line Added",
									life: 3000,
								});
							})
							.catch((error) => {});
					} else {
						toast.current.show({
							severity: "error",
							summary: "Duplicate Entry",
							detail: "Addition Failed",
							life: 3000,
						});
					}
				})
				.catch((error) => {});
		}
	};

	const confirmDeleteTieLine = (product) => {
		setdeleted_row_data(product);
		setdeleteDailog(true);
	};

	const exportCSV = () => {
		dt.current.exportCSV();
	};

	const table_header = () => {
		return (
			<div className="flex flex-wrap gap-2 align-items-center justify-content-between">
				<div className="flex flex-wrap gap-2">
					<Button
						size="small"
						severity="success"
						rounded
						raised
						label="Add New Tie Line"
						icon="pi pi-plus"
						onClick={openNew}
					/>
				</div>
				<span className="p-input-icon-left">
					<i className="pi pi-search" />

					<InputText
						col={20}
						value={globalFilterValue}
						onChange={onGlobalFilterChange}
						placeholder="Search"
					/>
				</span>
				<Button
					size="small"
					rounded
					raised
					label="Export to CSV"
					icon="pi pi-upload"
					className="p-button-help"
					onClick={exportCSV}
				/>
			</div>
		);
	};

	const deleteBodyTemplate = (rowData) => {
		return (
			<React.Fragment>
				<Button
					size="small"
					icon="pi pi-trash"
					rounded
					outlined
					severity="danger"
					onClick={() => confirmDeleteTieLine(rowData)}
				/>
			</React.Fragment>
		);
	};

	const new_element_dailog_footer = (
		<React.Fragment>
			{/* <Button
				size="small"
				severity="danger"
				rounded
				raised
				label="Cancel"
				icon="pi pi-times"
				outlined
				onClick={hideDialog}
			/> */}

			<ConfirmPopup
				target={buttonEl.current}
				visible={popupvisible}
				onHide={() => setpopupvisible(false)}
				message="Some Fields are Empty, Are you sure you want to proceed?"
				icon="pi pi-exclamation-triangle"
				accept={saveaccept}
				reject={savereject}
			/>
			<div className="card flex justify-content-center">
				<Button
					ref={buttonEl}
					size="small"
					severity="primary"
					rounded
					raised
					label="Save"
					icon="pi pi-check"
					onClick={() => {
						if (Feeder_Name_input && Feeder_Hindi_input) {
							if (
								!Feeder_From_input ||
								!Key_Far_End_input ||
								!Key_To_End_input ||
								!Meter_Far_End_input ||
								!Meter_To_End_input ||
								!To_Feeder_input
							) {
								setpopupvisible(true);
							} else {
								Save_Tie_line("All OK");
							}
						} else {
							alert("Names are Compulsory");
						}
					}}
				/>
			</div>
		</React.Fragment>
	);

	const cellClassName = (data) =>
		data ? (data.includes("No Key:") ? "p-max-min" : "") : "";

	return (
		<>
			<Fieldset hidden={!page_hide}>
				<div className="card flex justify-content-center">
					<h1>Please Login again by SSO</h1>
				</div>
			</Fieldset>

			<Divider align="left" hidden={page_hide}>
				<span
					className="p-tag"
					style={{
						backgroundColor: "#c77046",
						fontSize: "large",
						color: "#ffffff",
					}}
				>
					<Avatar
						icon="pi pi-table"
						style={{ backgroundColor: "#c77046", color: "#ffffff" }}
						shape="square"
					/>
					Mapping Table
				</span>
			</Divider>

			<ConfirmDialog
				visible={editDialog}
				onHide={() => seteditDialog(false)}
				message="Are you sure you want to save the details?"
				header="Confirmation"
				icon="pi pi-exclamation-triangle"
				accept={accept}
				reject={reject}
			/>

			<ConfirmDialog
				visible={deleteDailog}
				onHide={() => setdeleteDailog(false)}
				message="Are you sure you want to delete details?"
				header="Confirmation"
				icon="pi pi-exclamation-triangle"
				accept={accept1}
				reject={reject1}
			/>
			{/* <Fieldset
				legend={
					<div className="flex align-items-center ">
						<Avatar
							icon="pi pi-table"
							style={{ backgroundColor: "#000000", color: "#ffffff" }}
							shape="circle"
						/>
						<span className="font-bold ">Mapping Table</span>
					</div>
				}
			> */}

			<div hidden={page_hide}>
				<Toast ref={toast} />
				<div className="card">
					{/* <Toolbar
							className="mb-4"
							left={leftToolbarTemplate}
							right={rightToolbarTemplate}
						></Toolbar> */}

					<DataTable
						removableSort
						stripedRows
						showGridlines
						tableStyle={{ maxWidth: "100%" }}
						ref={dt}
						value={mapping_data_copy}
						editMode="row"
						dataKey="id"
						onRowEditComplete={onRowEditComplete}
						paginator
						rows={10}
						rowsPerPageOptions={[5, 10, 50, mapping_data_copy.length]}
						paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
						currentPageReportTemplate="Showing {first} to {last} of {totalRecords} Tie-Lines"
						filters={filters}
						globalFilterFields={[
							"Feeder_Name",
							"Key_To_End",
							"Key_Far_End",
							"Meter_To_End",
							"Meter_Far_End",
							"Feeder_From",
							"To_Feeder",
							"Feeder_Hindi",
						]}
						emptyMessage="You are Not Authorised."
						header={table_header}
						reorderableColumns
						size="small"
						cellClassName={cellClassName}
					>
						{/* <Column selectionMode="multiple" exportable={false}></Column> */}
						<Column
							alignHeader="center"
							// bodyStyle={{ textAlign: "center" }}
							field="Feeder_Name"
							header="Feeder Name"
							sortable
							style={{ minWidth: "16rem", maxWidth: "16rem" }}
							editor={(options) => textEditor(options)}
							headerClassName="p-head"
						></Column>
						<Column
							alignHeader="center"
							// bodyStyle={{ textAlign: "center" }}
							field="Feeder_Hindi"
							header="फीडर नाम"
							style={{ minWidth: "15rem", maxWidth: "15rem" }}
							editor={(options) => textEditor(options)}
							headerClassName="p-head"
						></Column>
						<Column
							alignHeader="center"
							bodyStyle={{ textAlign: "center" }}
							field="Feeder_From"
							header="To End Feeder"
							sortable
							style={{ minWidth: "8rem", maxWidth: "8rem" }}
							editor={(options) => textEditor(options)}
							headerClassName="p-head"
						></Column>
						<Column
							alignHeader="center"
							bodyStyle={{ textAlign: "center" }}
							field="Key_To_End"
							header="Key To End"
							sortable
							style={{ minWidth: "6rem", maxWidth: "6rem" }}
							editor={(options) => textEditor(options)}
							headerClassName="p-head"
						></Column>
						<Column
							alignHeader="center"
							bodyStyle={{ textAlign: "center" }}
							field="Meter_To_End"
							header="Meter To End"
							sortable
							style={{ minWidth: "6rem", maxWidth: "6rem" }}
							editor={(options) => textEditor(options)}
							headerClassName="p-head"
						></Column>
						<Column
							alignHeader="center"
							bodyStyle={{ textAlign: "center" }}
							field="To_Feeder"
							header="Far End Feeder"
							sortable
							style={{ minWidth: "8rem", maxWidth: "8rem" }}
							editor={(options) => textEditor(options)}
							headerClassName="p-head"
						></Column>
						<Column
							alignHeader="center"
							bodyStyle={{ textAlign: "center" }}
							field="Key_Far_End"
							header="Key Far End"
							sortable
							style={{ minWidth: "6rem", maxWidth: "6rem" }}
							editor={(options) => textEditor(options)}
							headerClassName="p-head"
						></Column>
						<Column
							alignHeader="center"
							bodyStyle={{ textAlign: "center" }}
							field="Meter_Far_End"
							header="Meter Far End"
							sortable
							style={{ minWidth: "7rem", maxWidth: "7rem" }}
							editor={(options) => textEditor(options)}
							headerClassName="p-head"
						></Column>
						<Column
							alignHeader="center"
							header="Edit"
							rowEditor
							headerStyle={{ minWidth: "1rem", maxWidth: "1rem" }}
							bodyStyle={{ textAlign: "center" }}
							headerClassName="p-head"
						></Column>

						<Column
							alignHeader="center"
							bodyStyle={{ textAlign: "center" }}
							header="Delete"
							body={deleteBodyTemplate}
							exportable={false}
							style={{ minWidth: "3rem", maxWidth: "3rem" }}
							headerClassName="p-head"
						></Column>
					</DataTable>
				</div>

				<Dialog
					visible={new_element_Dailog}
					style={{ width: "32rem" }}
					breakpoints={{ "960px": "75vw", "641px": "90vw" }}
					header="Add new Tie Line"
					modal
					className="p-fluid"
					footer={new_element_dailog_footer}
					onHide={hideDialog}
				>
					<div className="field">
						<label htmlFor="name" className="font-bold">
							Feeder Name
						</label>
						<InputText
							id="name"
							value={Feeder_Name_input}
							onChange={(e) => setFeeder_Name_input(e.target.value)}
							required

							// className={classNames({
							// 	"p-invalid": submitted && !product.name,
							// })}
						/>
						{submitted && !Feeder_Name_input && (
							<small className="p-error">Feeder Name is required.</small>
						)}
					</div>
					<div className="field">
						<label htmlFor="name" className="font-bold">
							फीडर नाम
						</label>
						<InputText
							id="name"
							value={Feeder_Hindi_input}
							onChange={(e) => setFeeder_Hindi_input(e.target.value)}
							required

							// className={classNames({
							// 	"p-invalid": submitted && !product.name,
							// })}
						/>
						{submitted && !Feeder_Hindi_input && (
							<small className="p-error">फीडर नाम देना अनिवार्य है</small>
						)}
					</div>

					<div className="flex flex-wrap gap-1 justify-content-between align-items-center">
						<div className="field">
							<label className="mb-3 font-bold">To End Feeder</label>
							<div className="formgrid grid">
								<InputText
									value={Feeder_From_input}
									onChange={(e) => setFeeder_From_input(e.target.value)}
									size={4}
								/>
							</div>
						</div>
						<div className="field">
							<label className="mb-3 font-bold">Key To End</label>
							<div className="formgrid grid">
								<InputText
									value={Key_To_End_input}
									onChange={(e) => setKey_To_End_input(e.target.value)}
									size={4}
								/>
							</div>
						</div>
						<div className="field">
							<label className="mb-3 font-bold">Meter To End</label>
							<div className="formgrid grid">
								<InputText
									value={Meter_To_End_input}
									onChange={(e) => setMeter_To_End_input(e.target.value)}
									size={4}
								/>
							</div>
						</div>
					</div>

					<div className="flex flex-wrap gap-1 justify-content-between align-items-center">
						<div className="field">
							<label className="mb-3 font-bold">Far End Feeder</label>
							<div className="formgrid grid">
								<InputText
									value={To_Feeder_input}
									onChange={(e) => setTo_Feeder_input(e.target.value)}
									size={2}
								/>
							</div>
						</div>
						<div className="field">
							<label className="mb-3 font-bold">Key Far End</label>
							<div className="formgrid grid">
								<InputText
									value={Key_Far_End_input}
									onChange={(e) => setKey_Far_End_input(e.target.value)}
									size={2}
								/>
							</div>
						</div>
						<div className="field">
							<label className="mb-3 font-bold">Meter Far End</label>
							<div className="formgrid grid">
								<InputText
									value={Meter_Far_End_input}
									onChange={(e) => setMeter_Far_End_input(e.target.value)}
									size={2}
								/>
							</div>
						</div>
					</div>
				</Dialog>
			</div>
			{/* </Fieldset> */}
		</>
	);
}
export default Mapping;
