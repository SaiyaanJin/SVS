import React from "react";
import moment from "moment";
import Plot from "react-plotly.js";

export default function SCADAgraph(props) {
  var name = "SCADA Data of ";
  var data = [];
  var datatype = "MW Data";

  if (props.scada_data && props.start_date && props.end_date) {
    for (var i = 1; i < props.scada_data.length; i++) {
      if (i === props.scada_data.length - 1) {
        name =
          name +
          props.scada_data[i]["Code"] +
          ": " +
          props.scada_data[i]["Name"];
        // name = name.slice(0, -1);
      } else {
        name =
          name +
          props.scada_data[i]["Code"] +
          ": " +
          props.scada_data[i]["Name"] +
          ", ";
      }

      let SCADA = {
        y: props.scada_data[i]["Data"],
        x: props.scada_data[0],

        name: props.scada_data[i]["Code"] + ": " + props.scada_data[i]["Name"],
        // " " +
        // moment(props.scada_data[i]["Date"][0]).format("DD-MM-YYYY"),

        type: "line",
      };

      data.push(SCADA);
    }
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
            color: "#009445",
          },
        },

        yaxis2: {
          title: "Frequency Data",

          titlefont: { color: "#8B0000", size: 18 },
          tickfont: { color: "#8B0000" },
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
