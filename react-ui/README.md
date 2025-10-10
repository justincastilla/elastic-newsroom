# Elastic News React UI

A React-based user interface for the Elastic News multi-agent workflow system. This UI allows you to create news articles by entering topic, angle, and word count, then watch as the AI agents collaborate in real-time to produce the article.

## Features

- **Simple Form Interface**: Enter topic, angle, word count, and priority
- **Real-time Workflow Monitoring**: See live updates as agents work
- **Agent Status Dashboard**: Monitor all 5 agents (News Chief, Reporter, Editor, Researcher, Publisher)
- **Workflow Progress**: Visual progress bar showing current step
- **Live Activity Updates**: See exactly what each agent is doing

## Prerequisites

- Node.js 16+ and npm
- Elastic News agents running on ports 8080-8084
- Environment variables configured

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage

1. **Start the News Agents**: Make sure all agents are running:
   ```bash
   ./start_newsroom.sh
   ```

2. **Open the UI**: Navigate to http://localhost:3000

3. **Create an Article**:
   - Enter a topic (e.g., "AI Agents Transform Modern Newsrooms")
   - Enter an angle (e.g., "How A2A protocol enables multi-agent collaboration")
   - Set word count (default: 1200)
   - Choose priority level
   - Click "Start News Workflow"

4. **Monitor Progress**: Watch as the agents work together:
   - **News Chief**: Coordinates the workflow
   - **Reporter**: Writes the article
   - **Editor**: Reviews content
   - **Researcher**: Gathers facts
   - **Publisher**: Publishes to Elasticsearch

## Architecture

### Components

- **WorkflowForm**: Input form for creating new articles
- **WorkflowProgress**: Visual progress tracking
- **AgentStatus**: Real-time agent monitoring
- **useWorkflowStatus**: Custom hook for polling agent status

### Services

- **newsroomService**: API client for communicating with agents
- Polls all agents every 2 seconds for real-time updates
- Handles errors gracefully

### Styling

- **Tailwind CSS**: Modern, responsive design
- **Lucide React**: Clean icons
- **Custom Components**: Reusable UI components

## API Endpoints

The UI communicates with the following agent endpoints:

- **News Chief** (8080): Story assignment and workflow coordination
- **Reporter** (8081): Article writing and status
- **Editor** (8082): Content review status
- **Researcher** (8083): Research progress
- **Publisher** (8084): Publication status

## Development

### Available Scripts

- `npm start`: Start development server
- `npm build`: Build for production
- `npm test`: Run tests
- `npm eject`: Eject from Create React App

### Environment Variables

The UI uses a proxy to communicate with the agents. Make sure the agents are running on the expected ports:

- News Chief: http://localhost:8080
- Reporter: http://localhost:8081
- Editor: http://localhost:8082
- Researcher: http://localhost:8083
- Publisher: http://localhost:8084

## Troubleshooting

### Common Issues

1. **Agents not responding**: Check that all agents are running
2. **CORS errors**: The UI uses a proxy to avoid CORS issues
3. **Workflow not starting**: Verify News Chief is accessible
4. **Status not updating**: Check browser console for errors

### Debug Mode

In development mode, the UI shows debug information including:
- Raw workflow progress data
- Agent status responses
- API communication logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Elastic News multi-agent system.
