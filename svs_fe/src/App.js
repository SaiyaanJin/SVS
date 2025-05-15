// import logo from "./logo.svg";
import { Avatar } from "primereact/avatar";
import { useState } from "react";
import React from "react";
import { BrowserRouter as Router, Route, Link, Routes } from "react-router-dom";
import "./App.css";
import "primeicons/primeicons.css";
import Sem_Data from "./Components/Sem_Data";
import Scada_Data from "./Components/Scada_Data";
import Dashboard from "./Components/Dashboard";
import SemVsScada from "./Components/SemVsScada";
import Mapping from "./Components/Mapping";

import axios from "axios";

axios.defaults.baseURL = process.env.REACT_APP_API_BASE_URL;

function App() {
	const [Dash, setDash] = useState(true);
	const [SemShow, setSemShow] = useState(true);
	const [ScadaShow, setScadaShow] = useState(true);
	const [ReportShow, setReportShow] = useState(true);
	const [MappingShow, setMappingShow] = useState(true);
	const [Token, setToken] = useState("");

	return (
		<div className="routes">
			<div
				className="shadow-class"
				style={{ marginTop: ".2%", marginBottom: "2%" }}
			>
				<img src="GI-Nav1.jpg" alt="posoco" style={{ width: "100%" }} />
			</div>

			<Router>
				<div
					className="list"
					style={{ fontSize: "x-small", marginTop: "1%", marginBottom: "-1%" }}
				>
					<ul
						hidden={Dash && SemShow && ScadaShow && ReportShow && MappingShow}
					>
						<Link to={"/?token=" + Token}>
							<Avatar
								icon="pi pi-home"
								style={{ backgroundColor: "#008668", color: "#ffffff" }}
								shape="circle"
							/>
							Dashboard
						</Link>

						<Link to={"Scada_Data?token=" + Token}>
							<Avatar
								icon="pi pi-bolt"
								style={{ backgroundColor: "#dc2626", color: "#ffffff" }}
								shape="circle"
							/>
							SCADA Data
						</Link>

						<Link to={"Sem_Data?token=" + Token}>
							<Avatar
								icon="pi pi-calculator"
								style={{ backgroundColor: "#065fc8", color: "#ffffff" }}
								shape="circle"
							/>
							Meter Data
						</Link>
						<Link to={"SemVsScada?token=" + Token}>
							<Avatar
								icon="pi pi-file-word"
								style={{ backgroundColor: "#000000", color: "#ffffff" }}
								shape="circle"
							/>
							SEM vs SCADA
						</Link>

						<Link to={"Mapping?token=" + Token}>
							<Avatar
								icon="pi pi-table"
								style={{ backgroundColor: "#c77046", color: "#ffffff" }}
								shape="circle"
							/>
							Mapping Table
						</Link>
						<Link to={"https://sso.erldc.in:3000"}>
							<Avatar
								icon="pi pi-sign-out"
								style={{ backgroundColor: "#ff3e1f", color: "#ffffff" }}
								shape="circle"
							/>
							Logout
						</Link>
					</ul>
					{/* </ul> */}
				</div>
				<Routes>
					<Route
						exact
						path="/"
						element={<Dashboard var1={setDash} var2={setToken} />}
					/>
					<Route
						exact
						path="Sem_Data"
						element={<Sem_Data var3={setSemShow} />}
					/>
					<Route
						exact
						path="Scada_Data"
						element={<Scada_Data var4={setScadaShow} />}
					/>
					<Route
						exact
						path="SemVsScada"
						element={<SemVsScada var5={setReportShow} />}
					/>
					<Route
						exact
						path="Mapping"
						element={<Mapping var6={setMappingShow} />}
					/>
				</Routes>
			</Router>
		</div>
	);
}
export default App;
