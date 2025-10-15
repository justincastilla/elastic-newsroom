import axios from 'axios';

const NEWS_CHIEF_URL = 'http://localhost:8080';

class NewsroomService {
  constructor() {
    this.client = axios.create({
      baseURL: NEWS_CHIEF_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async assignStory(storyData) {
    try {
      const response = await this.client.post('/assign-story', {
        action: 'assign_story',
        story: storyData
      });
      return response.data;
    } catch (error) {
      console.error('Error assigning story:', error);
      throw new Error(`Failed to assign story: ${error.message}`);
    }
  }

  async getStoryStatus(storyId) {
    try {
      const response = await this.client.post('/story-status', {
        action: 'get_story_status',
        story_id: storyId
      });
      return response.data;
    } catch (error) {
      console.error('Error getting story status:', error);
      throw new Error(`Failed to get story status: ${error.message}`);
    }
  }

  async getActiveStories() {
    try {
      const response = await this.client.post('/active-stories', {
        action: 'list_active_stories'
      });
      return response.data;
    } catch (error) {
      console.error('Error getting active stories:', error);
      return { active_stories: [] };
    }
  }

  // Note: Individual agent status endpoints removed in Phase 3
  // Status is now tracked via Event Hub SSE instead of polling
  async getReporterStatus(storyId) {
    // Return minimal stub - real status comes from Event Hub
    return { status: 'event_hub_only' };
  }

  async getEditorStatus(storyId) {
    // Return minimal stub - real status comes from Event Hub
    return { reviews: [] };
  }

  async getResearcherStatus(storyId) {
    // Return minimal stub - real status comes from Event Hub
    return { research_history: [] };
  }

  async getPublisherStatus(storyId) {
    // Return minimal stub - real status comes from Event Hub
    return { total_published: 0 };
  }

  async getAllAgentStatus(storyId) {
    try {
      const [newsChief, reporter, editor, researcher, publisher] = await Promise.allSettled([
        this.getStoryStatus(storyId),
        this.getReporterStatus(storyId),
        this.getEditorStatus(storyId),
        this.getResearcherStatus(storyId),
        this.getPublisherStatus(storyId)
      ]);

      return {
        newsChief: newsChief.status === 'fulfilled' ? newsChief.value : null,
        reporter: reporter.status === 'fulfilled' ? reporter.value : null,
        editor: editor.status === 'fulfilled' ? editor.value : null,
        researcher: researcher.status === 'fulfilled' ? researcher.value : null,
        publisher: publisher.status === 'fulfilled' ? publisher.value : null
      };
    } catch (error) {
      console.error('Error getting all agent status:', error);
      throw error;
    }
  }

  // Note: /clear-all endpoints removed in Phase 3
  // Agents are now stateless and track state internally
  async clearAllAgents() {
    // Return success stub - agents are stateless
    // User can refresh the page to reset UI state
    console.log('Agent clear requested - agents are now stateless, no action needed');
    return {
      status: 'success',
      message: 'Agents are stateless - refresh page to reset UI'
    };
  }
}

export default new NewsroomService();
