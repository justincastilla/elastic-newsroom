/**
 * Event Hub Client
 *
 * Connects to the Event Hub via Server-Sent Events (SSE) for real-time updates.
 * Replaces polling individual agent endpoints with a centralized event stream.
 *
 * Features:
 * - Automatic reconnection on disconnect
 * - Story-specific event filtering
 * - Event history replay on reconnect
 * - Heartbeat monitoring
 */

const EVENT_HUB_URL = process.env.REACT_APP_EVENT_HUB_URL || 'http://localhost:8090';

class EventHubClient {
  constructor() {
    this.eventSource = null;
    this.listeners = new Map(); // event_type -> [callback]
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000; // Start with 1 second
    this.storyId = null;
    this.lastEventTime = null;
  }

  /**
   * Connect to Event Hub SSE stream
   * @param {string|null} storyId - Optional filter to only receive events for specific story
   * @param {string|null} since - Optional ISO timestamp to replay events since that time
   */
  connect(storyId = null, since = null) {
    if (this.eventSource) {
      console.log('📡 Already connected to Event Hub');
      return;
    }

    this.storyId = storyId;

    // Build SSE URL with query parameters
    const params = new URLSearchParams();
    if (storyId) {
      params.append('story_id', storyId);
    }
    if (since) {
      params.append('since', since);
    } else if (this.lastEventTime) {
      // Automatically resume from last event time on reconnect
      params.append('since', this.lastEventTime);
    }

    const url = `${EVENT_HUB_URL}/stream${params.toString() ? '?' + params.toString() : ''}`;

    console.log(`📡 Connecting to Event Hub: ${url}`);

    try {
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log('✅ Event Hub connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this._emit('connected', { timestamp: new Date().toISOString() });
      };

      this.eventSource.onerror = (error) => {
        console.error('❌ Event Hub connection error:', error);
        this.isConnected = false;
        this._emit('error', error);
        this._attemptReconnect();
      };

      // Handle connection event
      this.eventSource.addEventListener('connection', (event) => {
        const data = JSON.parse(event.data);
        console.log('🔗 Event Hub connection established:', data);
        this._emit('connection', data);
      });

      // Handle heartbeat events (keep connection alive)
      this.eventSource.addEventListener('heartbeat', (event) => {
        const data = JSON.parse(event.data);
        this.lastEventTime = data.timestamp;
        // Don't emit heartbeats to listeners (internal only)
      });

      // Handle historical events (replayed on reconnect)
      this.eventSource.addEventListener('historical', (event) => {
        const data = JSON.parse(event.data);
        this.lastEventTime = data.timestamp;
        console.log(`📜 Historical event: ${data.event_type}`, data);
        this._emit(data.event_type, data);
        this._emit('*', data); // Emit to wildcard listeners
      });

      // Handle all agent events dynamically
      // Common event types from agents:
      const agentEventTypes = [
        'story_assigned',
        'research_started',
        'research_completed',
        'article_writing_started',
        'article_drafted',
        'review_started',
        'review_completed',
        'edits_applied',
        'publication_started',
        'file_saved',
        'elasticsearch_indexed',
        'publication_completed',
        'agent_event' // Generic fallback
      ];

      agentEventTypes.forEach(eventType => {
        this.eventSource.addEventListener(eventType, (event) => {
          const data = JSON.parse(event.data);
          this.lastEventTime = data.timestamp;
          console.log(`📨 ${eventType}:`, data);
          this._emit(eventType, data);
          this._emit('*', data); // Emit to wildcard listeners
        });
      });

      // Generic message handler for events without specific type
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.lastEventTime = data.timestamp;
          console.log('📨 Event (generic):', data);
          const eventType = data.event_type || 'message';
          this._emit(eventType, data);
          this._emit('*', data);
        } catch (error) {
          console.error('Error parsing SSE message:', error);
        }
      };

    } catch (error) {
      console.error('Error creating EventSource:', error);
      this._attemptReconnect();
    }
  }

  /**
   * Disconnect from Event Hub
   */
  disconnect() {
    if (this.eventSource) {
      console.log('🔌 Disconnecting from Event Hub');
      this.eventSource.close();
      this.eventSource = null;
      this.isConnected = false;
      this._emit('disconnected', { timestamp: new Date().toISOString() });
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  _attemptReconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      this._emit('max_reconnect_attempts', { attempts: this.reconnectAttempts });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000); // Max 30s

    console.log(`🔄 Reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    setTimeout(() => {
      this.connect(this.storyId);
    }, delay);
  }

  /**
   * Subscribe to specific event type
   * @param {string} eventType - Event type to listen for (use '*' for all events)
   * @param {Function} callback - Callback function(data)
   * @returns {Function} Unsubscribe function
   */
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);

    // Return unsubscribe function
    return () => this.off(eventType, callback);
  }

  /**
   * Unsubscribe from event type
   * @param {string} eventType - Event type
   * @param {Function} callback - Callback to remove
   */
  off(eventType, callback) {
    if (this.listeners.has(eventType)) {
      const callbacks = this.listeners.get(eventType);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to all registered listeners
   * @private
   */
  _emit(eventType, data) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Get connection status
   * @returns {boolean}
   */
  isConnectedToEventHub() {
    return this.isConnected;
  }

  /**
   * Reset reconnection state (useful for manual reconnect)
   */
  resetReconnect() {
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;
  }
}

// Export singleton instance
const eventHubClient = new EventHubClient();
export default eventHubClient;
