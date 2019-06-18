import React from 'react';
import ExpansionPanel from '@material-ui/core/ExpansionPanel';
import ExpansionPanelSummary from '@material-ui/core/ExpansionPanelSummary';
import Typography from '@material-ui/core/Typography';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import JobPanel from "../components/jobpanel.js"
import ExpansionPanelDetails from '@material-ui/core/ExpansionPanelDetails';
import Button from '@material-ui/core/Button';

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
      const commands = jobs
                        .map(row => row.command)
                        .reduce((acc, d) => acc.includes(d) ? acc : acc.concat(d), []);
      return (
        <div>
            {jobs
              .map(job => (
              <ExpansionPanel key={job.id}>
              <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}
                aria-controls="panel1a-content" key={job.command}>
                <Typography key={job.id}><pre><b>{job.command}</b></pre></Typography>
              </ExpansionPanelSummary>
              <JobPanel key={job.id} jobs={job.jobs}></JobPanel>
              </ExpansionPanel>
            ))}
        </div>
      );
  }
}

export default App;