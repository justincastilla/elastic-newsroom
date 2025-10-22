| #   | From       | To            | Action              | Protocol    | Description                                     |
  |-----|------------|---------------|---------------------|-------------|-------------------------------------------------|
  | 1   | User/UI    | News Chief    | Assign Story        | HTTP POST   | User submits story topic and angle              |
  | 2   | News Chief | Internal      | Create Story        | -           | Creates story record with unique ID             |
  | 3   | News Chief | Reporter      | Delegate Assignment | A2A         | Sends story assignment via A2A protocol         |
  | 4   | Reporter   | Internal      | Accept Assignment   | -           | Stores assignment internally                    |
  | 5   | Reporter   | Anthropic     | Generate Questions  | API         | Creates research questions                      |
  | 6   | Reporter   | Researcher    | Request Research    | A2A         | Sends questions (parallel with #7)              |
  | 7   | Reporter   | Archivist     | Search Archive      | A2A JSONRPC | Searches historical articles (parallel with #6) |
  | 8   | Researcher | Reporter      | Return Research     | A2A         | Returns research answers                        |
  | 9   | Archivist  | Reporter      | Return Archive      | A2A JSONRPC | Returns search results                          |
  | 10  | Reporter   | Anthropic     | Write Article       | API         | Generates article with research/context         |
  | 11  | Reporter   | Internal      | Store Draft         | -           | Saves draft internally                          |
  | 12  | Reporter   | Editor        | Submit Review       | A2A         | Sends article for editorial review              |
  | 13  | Editor     | Anthropic     | Review Article      | API         | Analyzes content, provides feedback             |
  | 14  | Editor     | Reporter      | Return Review       | A2A         | Sends editorial feedback                        |
  | 15  | Reporter   | Anthropic     | Apply Edits         | API         | Revises article based on feedback               |
  | 16  | Reporter   | Internal      | Update Draft        | -           | Updates draft with revisions                    |
  | 17  | Reporter   | Publisher     | Publish Article     | A2A         | Sends final article for publication             |
  | 18  | Publisher  | Elasticsearch | Index Article       | ES API      | Indexes article to search database              |
  | 19  | Publisher  | Filesystem    | Save Markdown       | File I/O    | Saves article as .md file                       |
  | 20  | Publisher  | Reporter      | Confirm Publication | A2A         | Returns success status                          |
  | 21  | Reporter   | News Chief    | Update Status       | Internal    | Updates status to "published"                   |
  | 22  | News Chief | User/UI       | Display Status      | HTTP        | UI displays final article                       |