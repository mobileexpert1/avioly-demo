import Foundation

struct RemoteConversationStreamingService: StreamingChatService {
    let endpoint: URL
    let session: URLSession

    init(endpoint: URL, session: URLSession = .shared) {
        self.endpoint = endpoint
        self.session = session
    }

    func stream(_ request: ChatStreamRequest) -> AsyncThrowingStream<ChatStreamEvent, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let chatService = RemoteConversationService(endpoint: endpoint, session: session)
                    let response = try await chatService.send(request.request)
                    continuation.yield(.metadata(response))
                    continuation.yield(.finished)
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }
}
