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

  async getReporterStatus(storyId) {
    try {
      const response = await axios.post('http://localhost:8081/get-status', {
        action: 'get_status',
        story_id: storyId
      });
      return response.data;
    } catch (error) {
      console.error('Error getting reporter status:', error);
      throw new Error(`Failed to get reporter status: ${error.message}`);
    }
  }

  async getEditorStatus(storyId) {
    try {
      const response = await axios.post('http://localhost:8082/get-status', {
        action: 'get_status',
        story_id: storyId
      });
      return response.data;
    } catch (error) {
      console.error('Error getting editor status:', error);
      return { reviews: [] };
    }
  }

  async getResearcherStatus(storyId) {
    try {
      const response = await axios.post('http://localhost:8083/get-status', {
        action: 'get_status',
        story_id: storyId
      });
      return response.data;
    } catch (error) {
      console.error('Error getting researcher status:', error);
      return { research_history: [] };
    }
  }

  async getPublisherStatus(storyId) {
    try {
      const response = await axios.post('http://localhost:8084/get-status', {
        action: 'get_status',
        story_id: storyId
      });
      return response.data;
    } catch (error) {
      console.error('Error getting publisher status:', error);
      return { total_published: 0 };
    }
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

  async clearAllAgents() {
    try {
      const agentUrls = [
        'http://localhost:8080', // News Chief
        'http://localhost:8081', // Reporter
        'http://localhost:8082', // Editor
        'http://localhost:8083', // Researcher
        'http://localhost:8084'  // Publisher
      ];

      const clearPromises = agentUrls.map(url => 
        axios.post(`${url}/clear-all`, {}, { timeout: 5000 })
          .catch(error => {
            console.warn(`Failed to clear agent at ${url}:`, error.message);
            return { status: 'error', message: error.message };
          })
      );

      const results = await Promise.all(clearPromises);
      
      const successCount = results.filter(result => result.status === 'success').length;
      console.log(`Cleared ${successCount}/${agentUrls.length} agents successfully`);
      
      return {
        status: 'success',
        message: `Cleared ${successCount}/${agentUrls.length} agents successfully`,
        results
      };
    } catch (error) {
      console.error('Error clearing agents:', error);
      return {
        status: 'error',
        message: error.message
      };
    }
  }
}

export default new NewsroomService();
