import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import moment from "moment";
import {jwtDecode } from "jwt-decode";
import { useLocation } from "react-router-dom";
import { Fieldset } from "primereact/fieldset";
import { Avatar } from "primereact/avatar";
import { Divider } from "primereact/divider";
import { Button } from "primereact/button";
import { BlockUI } from "primereact/blockui";

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
	const [isAdmin, setisAdmin] = useState(false);
	const [blocked, setBlocked] = useState(false);
	const [loading_show, setloading_show] = useState(false);

	useEffect(() => {
		if (id) {
			axios
				.post("http://10.3.230.62:5003/dashboard")
				.then((response) => {
					if (response.data) {
						setmeter_date({
							date: moment(response.data[0].meter_date[0].date).format(
								"DD-MM-YYYY"
							),
						});
						setscada_db_date({
							Date: moment(response.data[0].scada_db_date[0].Date).format(
								"DD-MM-YYYY"
							),
						});
						setmeter_folder_date(response.data[0].meter_folder_date);
					}
				})
				.catch((error) => {});

			params.var2(id);

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
								decoded["User"] === "00162" &&
								decoded["Person_Name"] === "Sanjay Kumar"
							) {
								setisAdmin(true);
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

	const folder_delete =()=>{
		axios
				.post("http://10.3.230.62:5003/folder_delete")
				.then((response) => {
					alert(response.data)
					setBlocked(false);
					setloading_show(false);
				})
				.catch((error) => {});
	}

	return (
		<>
		<div hidden={!loading_show}>
				<div className="loader">
					<div className="spinner"></div>
				</div>
			</div>
			<BlockUI blocked={blocked} fullScreen />

			<Fieldset hidden={!page_hide}>
				<div className="card flex justify-content-center">
					<h1>Please Login again by SSO</h1>
				</div>
			</Fieldset>

			<Divider align="left" hidden={page_hide}>
				<span
					className="p-tag"
					style={{ backgroundColor: "#000000", fontSize: "large" }}
				>
					<Avatar
						icon="pi pi-sitemap"
						style={{ backgroundColor: "#000000", color: "#ffffff" }}
						shape="square"
					/>
					Dashboard
				</span>
			</Divider>
			

			<div hidden={!page_hide} className="card flex justify-content-center">
				<marquee>
					Welcome &nbsp;
					<b>
						Sh. {Person_Name} ({User_id})
					</b>
					&nbsp; of &nbsp;<b>{Department}</b>
				</marquee>
			</div>

			<div hidden={!page_hide} className="flex flex-wrap gap-1 justify-content-between align-items-top">
			<div className="field"></div>
			<div className="field"></div>
			<div className="field">
				
				<DataTable value={[scada_db_date]}>
							<Column
								field="Date"
								header="Scada DB Up-To"
								style={{ width: "20%" }}
							></Column>
						</DataTable></div>
						<div className="field">
							<DataTable value={[meter_date]}>
							<Column
								field="date"
								header="Meter DB Up-To "
								style={{ width: "20%" }}
							></Column>
						</DataTable></div>
						<div className="field">
							<DataTable value={meter_folder_date}>
							<Column
								field="meter_folder_date"
								header="Meter Folder Up-To"
								style={{ width: "20%" }}
							></Column>
						</DataTable></div>
						<div className="field"><Button
								size="small"
								rounded
								raised
								// disabled={show_Skeleton}
								severity="danger"
								label="Delete Folder Files"
								icon="pi pi-delete-left"
								// text
								onClick={() => {folder_delete();setloading_show(true);setBlocked(true);}}
							/></div>
						<div className="field"></div>
						</div>
		</>
	);
}
export default Dashboard;
