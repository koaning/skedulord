import React from 'react';
import ExpansionPanel from '@material-ui/core/ExpansionPanel';
import ExpansionPanelSummary from '@material-ui/core/ExpansionPanelSummary';
import Typography from '@material-ui/core/Typography';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import JobPanel from "../components/jobpanel.js"
import Container from '@material-ui/core/Container';
import CssBaseline from '@material-ui/core/CssBaseline';
import Title from "../components/title.js";

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
        <div style={{ margin: `3rem auto`, maxWidth: 800 }}>
            <CssBaseline>
            <Container>
                <Title></Title>
                {jobs
                  .map(job => (
                  <ExpansionPanel key={job.id}>
                  <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}
                    aria-controls="panel1a-content" key={job.name}>
                    <Typography key={job.id}><b>{job.name}</b></Typography>
                  </ExpansionPanelSummary>
                  <JobPanel key={job.id} jobs={job.jobs}></JobPanel>
                  </ExpansionPanel>
                ))}
            </Container>
            </CssBaseline>
        </div>
      );
  }
}

export default App;