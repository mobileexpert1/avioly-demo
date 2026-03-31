import Foundation

protocol ConversationModuleDependencies {
    var conversationRepository: ConversationRepository { get }
    var chatService: ChatService { get }
    var conversationCache: ConversationCache { get }
}

struct ConversationModuleFactory {
    static func makeView(using dependencies: ConversationModuleDependencies) -> ConversationView {
        ConversationView(
            viewModel: ConversationViewModel(
                conversationRepository: dependencies.conversationRepository,
                conversationCache: dependencies.conversationCache,
                chatService: dependencies.chatService
            )
        )
    }
}
