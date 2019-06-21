import React from 'react';
import ExpansionPanelDetails from '@material-ui/core/ExpansionPanelDetails';
import Button from '@material-ui/core/Button';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';

export default function JobPanel(jobs) {
  console.log(jobs);
  return (
    <ExpansionPanelDetails>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>job id</TableCell>
              <TableCell align="right">start</TableCell>
              <TableCell align="right">end</TableCell>
              <TableCell align="right">logs</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {jobs.jobs.map(blob => (
              <TableRow key={blob.id}>
                <TableCell align="right">{blob.id}</TableCell>
                <TableCell align="right">{blob.startime}</TableCell>
                <TableCell align="right">{blob.endtime}</TableCell>
                <TableCell align="right"><Button variant="contained" size="small" key={blob.id}>logs</Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
    </ExpansionPanelDetails>)};


//        {job.jobs.map(blob =>
//           <Button variant="contained" color="primary" size="small" key={blob.id}>
//              {blob.endtime}
//           </Button>
//        )}