import Typography from '@/components/common/atoms/Typography';
import { HashtagList } from './HashtagList';
import { cn } from '@/lib/utils';

interface ContentItem {
  subtitle?: string;
  summary: string;
}

interface ReportSectionProps {
  title?: string; // 섹션 제목 (선택적)
  items: ContentItem[]; // 여러 subtitle-summary 쌍
  tags: string[];
  selectedTag?: string | null;
  onTagClick?: (tag: string | null) => void;
  className?: string;
}

function escapeHTML(s: string) {
  return s
    .replaceAll(/&/g, '&amp;')
    .replaceAll(/</g, '&lt;')
    .replaceAll(/>/g, '&gt;')
    .replaceAll(/"/g, '&quot;')
    .replaceAll(/'/g, '&#39;');
}

function buildHighlightHTML(summary: string, highlight: string | null) {
  if (!highlight) return escapeHTML(summary);

  // 1. 원본 텍스트에서 먼저 하이라이트 처리
  const escWord = highlight.replace(/[.*+?^${}()|[\]\\&]/g, '\\$&');
  const regex = new RegExp(`(${escWord})`, 'gi');

  // 2. 하이라이트 마커로 임시 치환 (HTML 이스케이프 전)
  const tempMarker = `__HIGHLIGHT_START__$1__HIGHLIGHT_END__`;
  const withMarkers = summary.replace(regex, tempMarker);

  // 3. HTML 이스케이프
  const safe = escapeHTML(withMarkers);

  // 4. 임시 마커를 실제 mark 태그로 교체
  return safe.replace(
    /__HIGHLIGHT_START__(.*?)__HIGHLIGHT_END__/g,
    '<mark class="bg-yellow-200 rounded px-0.5">$1</mark>',
  );
}

export default function ReportSection({
  title,
  items,
  tags,
  selectedTag = null,
  onTagClick,
  className = '',
}: ReportSectionProps) {
  const handleTagClick = (tag: string | null) => {
    onTagClick?.(tag);
  };

  return (
    <section className={cn('pb-4 mb-4 border-b border-slate-200 last:border-b-0', className)}>
      {/* 섹션 제목 - 있을 때만 표시 */}
      {title && (
        <Typography as="h2" variant="subtitle" weight="bold" className="mb-5">
          {title}
        </Typography>
      )}

      {/* 콘텐츠 아이템들 */}
      {items.map((item, idx) => {
        const html = buildHighlightHTML(item.summary, selectedTag);
        return (
          <div key={idx} className="mb-6 last:mb-0">
            {/* 소제목 - 있을 때만 표시 */}
            {item.subtitle && (
              <Typography as="p" variant="default" color="black" weight="semibold" className="mb-2">
                {item.subtitle}
              </Typography>
            )}
            {/* 본문 (선택 태그 하이라이트 반영) */}
            <div
              className="text-[16px] leading-relaxed tracking-normal font-normal text-[#757575]"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          </div>
        );
      })}

      {/* 태그 - 항상 표시 */}
      <HashtagList
        tags={tags}
        selectedTag={selectedTag}
        onTagClick={handleTagClick}
        className="mt-3"
      />
    </section>
  );
}
