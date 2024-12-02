import React from "react";
import moment from "moment";

import Plot from "react-plotly.js";

export default function SEMvsSCADAgraph(props) {
  var name = "SEM vs SCADA graph ";
  var data = [];
  var datatype = "MU Data";

  if (props.semvsscada_data && props.start_date && props.end_date) {
    console.log(props.semvsscada_data);
    let Meter = {
      y: props.semvsscada_data["Meter_data"][0]["modified_data"],
      x: props.semvsscada_data["Date_Time"],

      name:
        props.semvsscada_data["Meter_data"][0]["meterNO"] +
        " (" +
        props.semvsscada_data["Meter_data"][0]["meterID"] +
        ")",

      // " " +
      // moment(props.meter_data[i]["Date"][0]).format("DD-MM-YYYY"),

      type: "line",
    };

    data.push(Meter);

    let SCADA = {
      y: props.semvsscada_data["Scada_data"][0]["Data"],
      x: props.semvsscada_data["Date_Time"],

      name:
        props.semvsscada_data["Scada_data"][0]["Code"] +
        ": " +
        props.semvsscada_data["Scada_data"][0]["Name"],
      // " " +
      // moment(props.scada_data[i]["Date"][0]).format("DD-MM-YYYY"),

      type: "line",
    };

    data.push(SCADA);

    let SEMvsSCADA = {
      y: props.semvsscada_data["Percentage_diff"],
      x: props.semvsscada_data["Date_Time"],
      yaxis: "y2",
      marker: { color: "#99c794" },
      name:
        props.semvsscada_data["Meter_data"][0]["meterNO"] +
        " (" +
        props.semvsscada_data["Meter_data"][0]["meterID"] +
        ")" +
        " vs " +
        props.semvsscada_data["Scada_data"][0]["Code"] +
        ": " +
        props.semvsscada_data["Scada_data"][0]["Name"],
      // " " +
      // moment(props.scada_data[i]["Date"][0]).format("DD-MM-YYYY"),

      type: "line",
    };

    data.push(SEMvsSCADA);
  }

  return (
    <Plot
      data={data}
      onClick={(d) => {
        alert(
          d.points[0].y +
            " at " +
            d.points[0].x +
            " of " +
            d.points[0].data["name"]
        );
      }}
      layout={{
        showlegend: true,
        legend: {
          font: {
            family: "Courier New, monospace",
            size: 14,
            color: "#7f7f7f",
          },
          orientation: "h",
          bgcolor: "white",
          xanchor: "center",
          yanchor: "center",
          y: -0.5,
          x: 0.5,
        },
        width: 1898,
        height: 600,
        title: name,
        xaxis: {
          title: "Dates",
          titlefont: {
            family: "Courier New, monospace",
            size: 18,
            color: "#7f7f7f",
          },
          tickfont: { color: "#7f7f7f", size: 9 },
        },
        yaxis: {
          title: datatype,
          titlefont: {
            size: 18,
            color: "#e37034",
          },
        },

        yaxis2: {
          title: "SEM vs SCADA (%)",

          titlefont: { color: "#99c794", size: 18 },
          tickfont: { color: "#99c794" },
          anchor: "free",
          overlaying: "y",
          side: "right",
          position: 1,
        },
        xaxis2: {
          title: "Duration Curve",
          titlefont: { color: "rgb(148, 103, 189)" },
          tickfont: { color: "rgb(148, 103, 189)" },
          overlaying: "x",
          side: "top",
        },
      }}
    />
  );
}
