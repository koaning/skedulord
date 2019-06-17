import React from 'react';
import ExpansionPanel from '@material-ui/core/ExpansionPanel';
import ExpansionPanelSummary from '@material-ui/core/ExpansionPanelSummary';
import ExpansionPanelDetails from '@material-ui/core/ExpansionPanelDetails';
import Typography from '@material-ui/core/Typography';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import Button from '@material-ui/core/Button';
import JobPanel from "../components/jobpanel.js"

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
      console.log(jobs);
      console.log(commands);
      return (
        <div>
            {commands
              .map(job => (
              <ExpansionPanel key={job}>
              <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}
                aria-controls="panel1a-content" key={job.id}>
                <Typography key={job.id}><pre><b>{job}</b></pre></Typography>
              </ExpansionPanelSummary>
              <JobPanel></JobPanel>
              </ExpansionPanel>
            ))}
        </div>
      );
  }
}

export default App;