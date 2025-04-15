***REMOVED***
    <LayoutCenterPanel>
      ***REMOVED***
  ***REMOVED***class="mcp-client">
                <h1>MCP Client</h1>
                <p>Connection Status: {{ connectionStatus ***REMOVED******REMOVED***</p>

                <!-- 输入框和按钮 -->
                <div>
                    <input
                        v-model="message"
                        style="width: 280px; height: 25px"
                        placeholder="Enter message to send"
          ***REMOVED***
                    <button
                        @click="sendMessage"
                        style="height: 25px; margin-left: 2px; width: 80px"
          ***REMOVED***
                        Send
          ***REMOVED***
    ***REMOVED***

                <!-- 消息日志 -->
      ***REMOVED***class="message-log">
                    <h3>Message Log:</h3>
                    <ul>
                      ***REMOVED***{
                            messages
                        ***REMOVED******REMOVED***
                    </ul>
    ***REMOVED***
***REMOVED***
      ***REMOVED***
    </LayoutCenterPanel>
***REMOVED***

<script lang="tsx" setup>
***REMOVED***
***REMOVED*** // 假设存在 SseClientTransport

const message = ref(''***REMOVED***
const messages = ref(''***REMOVED***
const connectionStatus = ref('Disconnected'***REMOVED***
//https://github.com/modelcontextprotocol/typescript-sdk
// StdioClientTransport
***REMOVED***new URL('http://localhost:8000/sse'***REMOVED******REMOVED***

***REMOVED***
  ***REMOVED***
    ***REMOVED***
        version: '1.0.0'
    ***REMOVED***,
  ***REMOVED***
    ***REMOVED***
            prompts: {***REMOVED***,
            resources: {***REMOVED***,
            tools: {***REMOVED***
        ***REMOVED***
    ***REMOVED***
***REMOVED***

onMounted(async (***REMOVED*** => {
    await client.connect(transport***REMOVED***
    connectionStatus.value = 'Connected'
    const tools = await client.listTools(***REMOVED***
    console.log(tools***REMOVED***

    // const prompts = await client.listPrompts(***REMOVED***
    // console.log(prompts***REMOVED***
***REMOVED******REMOVED***

const sendMessage = async (***REMOVED*** => {
 ***REMOVED***
        name: 'get_weather',
        arguments: {
            location: message.value
        ***REMOVED***
    ***REMOVED******REMOVED***
    messages.value = JSON.stringify(result.content***REMOVED***
    console.log(result.content***REMOVED***
***REMOVED***

// List prompts
// const prompts = await client.listPrompts(***REMOVED***

// // Get a prompt
// const prompt = await client.getPrompt('example-prompt', {
//     arg1: 'value'
// ***REMOVED******REMOVED***

// List resources
// const resources = await client.listResources(***REMOVED***

// // Read a resource
// const resource = await client.readResource('file:///example.txt'***REMOVED***
***REMOVED***

***REMOVED***
.mcp-client {
    font-family: Arial, sans-serif;
    max-width: 600px;
  ***REMOVED***
  ***REMOVED***
    border: 1px solid #ccc;
  ***REMOVED***
    margin-top: 200px;
***REMOVED***

.message-log {
    margin-top: 20px;
***REMOVED***

ul {
    list-style-type: none;
  ***REMOVED***
***REMOVED***

li {
    background: #f9f9f9;
    margin: 5px 0;
  ***REMOVED***
  ***REMOVED***
  ***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
  ***REMOVED***
  ***REMOVED***
  ***REMOVED***
    margin-right: 2px;
    background-color: #ffffff;
***REMOVED***
***REMOVED***
