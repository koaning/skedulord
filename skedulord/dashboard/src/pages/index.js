import React from "react"

import Title from "../components/title"
import ControlledExpansionPanels from "../components/bar"
import Modal from "../components/modal"

const IndexPage = () => (
  <div>
    <Title></Title>
    <ControlledExpansionPanels></ControlledExpansionPanels>
    <p>Welcome to your new Gatsby site.</p>
    <Modal></Modal>
  </div>
)

export default IndexPage
