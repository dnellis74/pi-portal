import { useNavigate } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';

import { AgGridReact } from '@ag-grid-community/react'; // React Grid Logic
import "@ag-grid-community/styles/ag-grid.css"; // Core CSS
import "@ag-grid-community/styles/ag-theme-material.css"; // Theme

import { ColDef, ModuleRegistry } from '@ag-grid-community/core';
import { ClientSideRowModelModule } from '@ag-grid-community/client-side-row-model';

ModuleRegistry.registerModules([ClientSideRowModelModule]);

/*eslint-disable*/
function parseJwt(token) {
  var base64Url = token.split('.')[1];
  var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
  }).join(''));
  return JSON.parse(jsonPayload);
}

const LinkCellRenderer = (props) => {
  const cellValue = props.value;
  const url = `${props.data.id}`; // Adjust the URL as needed

  return (
    <a href={url} onClick={(e) => {
      e.preventDefault();
      // Handle click event, e.g. navigation
      console.log(`Clicked link for ${cellValue}`);
    }}>
      {cellValue}
    </a>
  );
};

// Row Data Interface
interface IRow {
  updated: string;
  count_by_state: number;
  State: string;
  epa_region: number;
  Regulation: string;
  Description: string;
  Link: string;
}

const PolicyTable = () => {
  // Row Data: The data to be displayed.
  const [rowData, setRowData] = useState<IRow[]>([]);

  const LinkCellRenderer = (props) => {
    return <a href={props.data.Link} target="_blank"> {props.data.Regulation} </a>;
  };

  // Column Definitions: Defines & controls grid columns.
  const [colDefs] = useState<ColDef[]>([
    {
      field: "updated",
      headerName: "Updated"
    },
    {
      field: "count_by_state",
      headerName: "Count By State"
    },
    { field: "State" },
    {
      field: "epa_region",
      headerName: "EPA Region"
    },
    {
      headerName: "Regulation",
      cellRenderer: LinkCellRenderer
    },
    { field: "Description" }
  ]);

  // Apply settings across all columns
  const defaultColDef = useMemo<ColDef>(() => {
    return {
      filter: true
    };
  }, []);

  // Fetch data & update rowData state
  useEffect(() => {
    fetch('/documents.json') // Fetch data from server
      .then(result => result.json()) // Convert to JSON
      .then(rowData => setRowData(rowData)) // Update state of `rowData`
  }, [])

  // Container: Defines the grid's theme & dimensions.
  return (
    <div className={"ag-theme-material"} style={{ width: 1048, height: 500 }}>
      {/* The AG Grid component, with Row Data & Column Definition props */}
      <AgGridReact
        rowData={rowData}
        columnDefs={colDefs}
        defaultColDef={defaultColDef}
        pagination={true}
      />
    </div>
  );
}

const HomePage = () => {
  const navigate = useNavigate();
  var idToken = parseJwt(sessionStorage.idToken.toString());
  var accessToken = parseJwt(sessionStorage.accessToken.toString());
  console.log("Amazon Cognito ID token encoded: " + sessionStorage.idToken.toString());
  console.log("Amazon Cognito ID token decoded: ");
  console.log(idToken);
  console.log("Amazon Cognito access token encoded: " + sessionStorage.accessToken.toString());
  console.log("Amazon Cognito access token decoded: ");
  console.log(accessToken);
  console.log("Amazon Cognito refresh token: ");
  console.log(sessionStorage.refreshToken);
  console.log("Amazon Cognito example application. Not for use in production applications.");
  const handleLogout = () => {
    sessionStorage.clear();
    navigate('/login');
  };

  return (
    <div>
      <img src="/PI-Logo.png" width="300px"/>
      <PolicyTable />

      <button onClick={handleLogout}>Logout</button>
      <p>See console log for Amazon Cognito user tokens.</p>
    </div>
  );
};

export default HomePage;
