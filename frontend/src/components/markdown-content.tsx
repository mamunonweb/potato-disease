import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownContentProps {
  children: string
}

export function MarkdownContent({ children }: MarkdownContentProps) {
  return (
    <div className="[&_code]:bg-background/60 [&_pre]:bg-background/60 text-sm leading-relaxed [&_a]:underline [&_a]:underline-offset-2 [&_code]:rounded [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-[0.8em] [&_h1]:mt-2 [&_h1]:mb-1 [&_h1]:text-base [&_h1]:font-semibold [&_h1]:first:mt-0 [&_h2]:mt-2 [&_h2]:mb-1 [&_h2]:text-[15px] [&_h2]:font-semibold [&_h2]:first:mt-0 [&_h3]:mt-2 [&_h3]:mb-1 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:first:mt-0 [&_hr]:my-2 [&_li]:mt-1 [&_li]:first:mt-0 [&_ol]:my-1 [&_ol]:list-decimal [&_ol]:pl-5 [&_pre]:my-1 [&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:p-2 [&_pre]:text-xs [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_strong]:font-semibold [&_table]:my-1 [&_table]:w-full [&_table]:text-xs [&_td]:border-b [&_td]:px-1 [&_td]:py-0.5 [&_td]:align-top [&_th]:border-b [&_th]:px-1 [&_th]:py-0.5 [&_th]:text-left [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-5">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
