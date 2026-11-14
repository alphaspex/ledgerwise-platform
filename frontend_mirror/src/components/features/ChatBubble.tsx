/**
 * Inputs :
 *   - props: { message: ThreadMessage }
 *   - ToolCallChip component
 * Outputs :
 *   - JSX.Element (bubble aligned left for prospect, right for agent/human; sender label (Prospect / Agent / Human), body rendered as PLAIN TEXT only (never dangerouslySetInnerHTML), timestamp, and one ToolCallChip per item of tool_calls under the bubble; entrance animation)
 * File explanation : One message of a conversation.
 */
