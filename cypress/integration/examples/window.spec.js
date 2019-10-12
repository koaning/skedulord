/// <reference types="Cypress" />

context('Window', () => {
  beforeEach(() => {
    cy.visit('http://0.0.0.0:5000')
  })

  it('there should be a logo', () => {
    cy.get("img")
  })

  it('the first box works', () => {
    cy.get("b").first().click()
    cy.get('a.MuiButtonBase-root').first().click()
    console.log(cy.get("b"))
  })

  it('the second box works', () => {
    cy.get("b").last().click()
    cy.get('a.MuiButtonBase-root').last().click()
    console.log(cy.get("b"))
  })
})
