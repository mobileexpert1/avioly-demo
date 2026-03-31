import XCTest
@testable import AvioFly

final class ConversationViewModelTests: XCTestCase {
    func testLoadDashboardLoadsThreadHistory() async {
        let repository = RecordingConversationRepository(
            pageResult: ConversationPageResult(
                items: [
                    ConversationThread(id: "thread-1", title: "Previous inquiry", updatedAt: Date(), preview: "Preview one")
                ],
                nextCursor: "cursor-2",
                hasMore: true
            )
        )
        let viewModel = ConversationViewModel(
            conversationRepository: repository,
            conversationCache: TestConversationCache(),
            chatService: TestChatService()
        )

        await viewModel.loadDashboard()

        XCTAssertEqual(viewModel.threads.count, 1)
        XCTAssertEqual(viewModel.threads.first?.title, "Previous inquiry")
        XCTAssertEqual(viewModel.hasMoreThreads, true)
        XCTAssertEqual(repository.requestedPages.count, 1)
    }

    func testLoadMoreThreadsAppendsResults() async {
        let repository = RecordingConversationRepository(
            pageResult: ConversationPageResult(
                items: [
                    ConversationThread(id: "thread-1", title: "Initial", updatedAt: Date(), preview: nil)
                ],
                nextCursor: "cursor-2",
                hasMore: true
            ),
            nextPageResult: ConversationPageResult(
                items: [
                    ConversationThread(id: "thread-2", title: "Older", updatedAt: Date(), preview: "Older preview")
                ],
                nextCursor: nil,
                hasMore: false
            )
        )
        let viewModel = ConversationViewModel(
            conversationRepository: repository,
            conversationCache: TestConversationCache(),
            chatService: TestChatService()
        )

        await viewModel.loadDashboard()
        await viewModel.loadMoreThreads()

        XCTAssertEqual(viewModel.threads.count, 2)
        XCTAssertEqual(viewModel.threads.last?.title, "Older")
        XCTAssertEqual(viewModel.hasMoreThreads, false)
        XCTAssertEqual(repository.requestedPages.count, 2)
    }

    func testSendMessageAppendsUserAndAssistantMessages() async {
        let viewModel = ConversationViewModel(
            conversationRepository: RecordingConversationRepository(),
            conversationCache: TestConversationCache(),
            chatService: TestChatService()
        )

        await viewModel.loadDashboard()
        await viewModel.sendMessage("Check account status")

        XCTAssertEqual(viewModel.messages.count, 2)
        XCTAssertEqual(viewModel.messages.first?.role, .user)
        XCTAssertEqual(viewModel.messages.last?.role, .assistant)
        XCTAssertEqual(viewModel.assistantConfidence, 0.91, accuracy: 0.001)
        XCTAssertEqual(viewModel.suggestedActions, ["Refine request"])
        XCTAssertEqual(viewModel.currentResponseKind, .options)
        XCTAssertEqual(viewModel.currentOptions.count, 2)
    }

    func testSelectModeUpdatesActiveMode() {
        let viewModel = ConversationViewModel(
            conversationRepository: RecordingConversationRepository(),
            conversationCache: TestConversationCache(),
            chatService: TestChatService()
        )

        viewModel.selectMode(.expert)

        XCTAssertEqual(viewModel.activeMode, .expert)
    }

    func testSendMessageIgnoresWhitespaceOnlyInput() async {
        let viewModel = ConversationViewModel(
            conversationRepository: RecordingConversationRepository(),
            conversationCache: TestConversationCache(),
            chatService: TestChatService()
        )

        await viewModel.sendMessage("   ")

        XCTAssertTrue(viewModel.messages.isEmpty)
    }

    func testCancelCurrentSendStopsInFlightRequest() async {
        let viewModel = ConversationViewModel(
            conversationRepository: RecordingConversationRepository(),
            conversationCache: TestConversationCache(),
            chatService: SlowChatService()
        )

        let task = Task {
            await viewModel.sendMessage("please cancel")
        }

        await Task.yield()
        viewModel.cancelCurrentSend()
        await task.value

        XCTAssertFalse(viewModel.isSendingMessage)
    }

    func testSendMessageUsesCachedResponseWhenAvailable() async {
        let cache = TestConversationCache()
        let viewModel = ConversationViewModel(
            conversationRepository: RecordingConversationRepository(),
            conversationCache: cache,
            chatService: TestChatService()
        )

        await cache.storeResponse(
            ChatResponse(
                kind: .text,
                reply: "Cached reply.",
                suggestedActions: ["Open cache"],
                options: [],
                confidence: 0.77,
                artifacts: [],
                reasoningSummary: "Cached path.",
                safetyNotice: nil,
                streamingSupported: true
            ),
            for: "concierge::Check account status::root::20"
        )

        await viewModel.sendMessage("Check account status")

        XCTAssertEqual(viewModel.messages.count, 2)
        XCTAssertEqual(viewModel.messages.last?.content, "Cached reply.")
        XCTAssertEqual(viewModel.assistantConfidence, 0.77, accuracy: 0.001)
    }
}

private final class RecordingConversationRepository: ConversationRepository {
    let pageResult: ConversationPageResult
    let nextPageResult: ConversationPageResult?
    private(set) var requestedPages: [ConversationPage] = []

    init(pageResult: ConversationPageResult = .init(items: [], nextCursor: nil, hasMore: false), nextPageResult: ConversationPageResult? = nil) {
        self.pageResult = pageResult
        self.nextPageResult = nextPageResult
    }

    func loadThreads(page: ConversationPage) async throws -> ConversationPageResult {
        requestedPages.append(page)
        if requestedPages.count == 1 {
            return pageResult
        }
        return nextPageResult ?? .init(items: [], nextCursor: nil, hasMore: false)
    }
}

private struct TestChatService: ChatService {
    func send(_ request: ChatRequest) async throws -> ChatResponse {
        ChatResponse(
            kind: .options,
            reply: "I can help with that.",
            suggestedActions: ["Refine request"],
            options: [
                ChatOption(id: "opt-1", title: "Option one", value: "Open account details"),
                ChatOption(id: "opt-2", title: "Option two", value: "Show recent activity")
            ],
            confidence: 0.91,
            artifacts: [
                ChatArtifact(id: UUID(), title: "Signal", value: "High clarity", kind: .signal)
            ],
            reasoningSummary: "Mocked response for test coverage.",
            safetyNotice: nil,
            streamingSupported: true
        )
    }
}

private struct SlowChatService: ChatService {
    func send(_ request: ChatRequest) async throws -> ChatResponse {
        try await Task.sleep(nanoseconds: 500_000_000)
        return ChatResponse(
            kind: .text,
            reply: "Slow response.",
            suggestedActions: [],
            options: [],
            confidence: 0.5,
            artifacts: [],
            reasoningSummary: "Slow path.",
            safetyNotice: nil,
            streamingSupported: true
        )
    }
}

private actor TestConversationCache: ConversationCache {
    private var threads: [String: ConversationPageResult] = [:]
    private var responses: [String: ChatResponse] = [:]

    func cachedThreads(for page: ConversationPage) async -> ConversationPageResult? {
        threads["\(page.cursor ?? "root")::\(page.limit)"]
    }

    func storeThreads(_ result: ConversationPageResult, for page: ConversationPage) async {
        threads["\(page.cursor ?? "root")::\(page.limit)"] = result
    }

    func cachedResponse(for key: String) async -> ChatResponse? {
        responses[key]
    }

    func storeResponse(_ response: ChatResponse, for key: String) async {
        responses[key] = response
    }
}
