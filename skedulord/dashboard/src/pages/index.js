import React from "react"
import { Link } from "gatsby"

import Image from "../components/image"
import Title from "../components/title"
import ControlledExpansionPanels from "../components/bar"

const IndexPage = () => (
  <div>
    <Title></Title>
    <ControlledExpansionPanels></ControlledExpansionPanels>
    <p>Welcome to your new Gatsby site.</p>
  </div>
)

export default IndexPage
