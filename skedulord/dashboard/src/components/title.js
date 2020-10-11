import React from "react"
import { makeStyles } from "@material-ui/core/styles"
import Paper from "@material-ui/core/Paper"
import Typography from "@material-ui/core/Typography"
// import logo from "../../../images/logo2.jpg"
import Img from "gatsby-image"
import { useStaticQuery, graphql } from "gatsby"

const useStyles = makeStyles(theme => ({
  root: {
    padding: theme.spacing(3, 2),
  },
}))

export default function PaperSheet({}) {
  const classes = useStyles()
  const data = useStaticQuery(graphql`
    query MyQuery {
      file(relativePath: { eq: "skedulord.png" }) {
        childImageSharp {
          fluid {
            aspectRatio
            base64
            sizes
            src
            srcSet
          }
        }
      }
    }
  `)

  return (
    <div>
      <Paper className={classes.root}>
        <Typography variant="h5" component="h3" align="center">
          <Img fluid={data.file.childImageSharp.fluid} alt="Logo" />
        </Typography>
      </Paper>
    </div>
  )
}
