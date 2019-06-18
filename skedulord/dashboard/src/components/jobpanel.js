import React from 'react';
import ExpansionPanelDetails from '@material-ui/core/ExpansionPanelDetails';
import Button from '@material-ui/core/Button';

export default function JobPanel(jobs) {
  console.log(jobs);
  return (
    <ExpansionPanelDetails>
        {jobs.jobs.map(blob => (
            <Button variant="contained" color="primary" size="small" key={blob.id}>
              {blob.endtime}
            </Button>
        ))}
    </ExpansionPanelDetails>)};


//        {job.jobs.map(blob =>
//           <Button variant="contained" color="primary" size="small" key={blob.id}>
//              {blob.endtime}
//           </Button>
//        )}