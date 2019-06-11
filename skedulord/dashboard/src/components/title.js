import React from "react"
import { css } from "@emotion/core"

const title = css`
  text-align: center;
`

export default ({ children }) => (
    <div css={title}>
        <h1>skedulord</h1>
    </div>
)
