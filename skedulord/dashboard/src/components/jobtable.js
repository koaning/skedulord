import React from 'react';
import { makeStyles } from '@material-ui/core/styles';

import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';


class App extends React.Component {
  constructor() {
    super();
    this.state = {
      value: 1,
      jobs: []
    };
  }

  componentDidMount() {
    fetch('/api/heartbeats')
      .then(response => response.json())
      .then(data => this.setState({jobs: data}));
  }

  render(){
    const jobs = this.state.jobs;
    console.log(jobs);


    return (
      <div>
      <Paper>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell><b>Command</b></TableCell>
            <TableCell align="right"><b>Started</b></TableCell>
            <TableCell align="right"><b>Finished</b></TableCell>
            <TableCell align="right"><b>Status(g)</b></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {jobs.map(row => (
            <TableRow key={row.id}>
              <TableCell component="th" scope="row">
                <pre>{row.command}</pre>
              </TableCell>
              <TableCell align="right">{row.startime}</TableCell>
              <TableCell align="right">{row.endtime}</TableCell>
              <TableCell align="right">{row.command}</TableCell>
            </TableRow>
          ))}
        </TableBody>
        </Table>
        </Paper>
      </div>
    )
  }
}

export default App;