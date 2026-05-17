const form = document.querySelector('#question-form')
const questionInput = document.querySelector('#question')
const submitButton = document.querySelector('#submit-button')
const statusNode = document.querySelector('#status')
const answerNode = document.querySelector('#answer')
const traceNode = document.querySelector('#trace')
const skillsNode = document.querySelector('#skills')
const mcpServersNode = document.querySelector('#mcp-servers')

function setStatus (message) {
  statusNode.textContent = message
}

function renderList (node, items, renderItem) {
  node.innerHTML = ''

  for (const item of items) {
    const listItem = document.createElement('li')
    listItem.textContent = renderItem(item)
    node.appendChild(listItem)
  }
}

async function loadRegistrySummary () {
  const response = await fetch('/api/registry-summary')
  const data = await response.json()

  renderList(skillsNode, data.skills || [], (skill) => {
    return `${skill.name}: ${skill.summary}`
  })

  renderList(mcpServersNode, data.mcpServers || [], (server) => {
    return `${server.name} (${server.transport}): ${server.purpose}`
  })
}

async function askQuestion (question) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'content-type': 'application/json'
    },
    body: JSON.stringify({ question })
  })
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.error || 'Request failed')
  }

  return data
}

form.addEventListener('submit', async (event) => {
  event.preventDefault()

  const question = questionInput.value.trim()

  if (!question) {
    setStatus('Please enter a question.')
    return
  }

  submitButton.disabled = true
  answerNode.textContent = 'Running...'
  traceNode.textContent = 'Collecting trace...'
  setStatus('Calling agent...')

  try {
    const result = await askQuestion(question)

    answerNode.textContent = result.answer || '(empty answer)'
    traceNode.textContent = JSON.stringify(result.trace, null, 2)
    setStatus('Done')
  } catch (error) {
    answerNode.textContent = error.message
    traceNode.textContent = 'No trace available.'
    setStatus('Request failed')
  } finally {
    submitButton.disabled = false
  }
})

loadRegistrySummary().catch((error) => {
  answerNode.textContent = error.message
  setStatus('Failed to load registries')
})
