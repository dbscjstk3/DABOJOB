import { useState } from 'react';
import Typography from '@/components/common/atoms/Typography';
import ReportSection from '../molecules/ReportSection';
import { cn } from '@/lib/utils';

interface Section {
  title?: string; // 섹션 제목 (선택적)
  items: Array<{
    subtitle?: string;
    summary: string;
  }>;
  tags: string[];
}

interface ReportContainerProps {
  title: string;
  sections: Section[];
  onTagSelect?: (tag: string | null) => void;
  className?: string;
}

export default function ReportContainer({
  title,
  sections,
  onTagSelect,
  className = '',
}: ReportContainerProps) {
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [selectedSection, setSelectedSection] = useState<number | null>(null);
  const [expanded, setExpanded] = useState(false);

  const handleTagClick = (sectionIdx: number, tag: string | null) => {
    if (selectedTag === tag && selectedSection === sectionIdx) {
      setSelectedTag(null);
      setSelectedSection(null);
      onTagSelect?.(null);
    } else {
      setSelectedTag(tag);
      setSelectedSection(sectionIdx);
      onTagSelect?.(tag);
    }
  };

  return (
    <article className={cn('rounded-xl border border-slate-200 bg-white p-4 md:p-6', className)}>
      {/* 제목 */}
      <Typography
        as="h1"
        variant="title"
        weight="bold"
        className="mb-7 p-1 bg-blue-50"
        align="center"
      >
        ✨ {title} ✨
      </Typography>

      {/* 섹션들 */}
      <div className={cn('relative', expanded ? '' : 'max-h-[500px] overflow-hidden')}>
        {sections.map((section, idx) => (
          <ReportSection
            key={idx}
            title={section.title ? `${idx + 1}. ${section.title}` : undefined}
            items={section.items}
            tags={section.tags}
            selectedTag={selectedSection === idx ? selectedTag : null}
            onTagClick={(tag) => handleTagClick(idx, tag)}
          />
        ))}

        {/* 그라데이션 효과 (접혀있을 때) */}
        {!expanded && (
          <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white to-transparent pointer-events-none" />
        )}
      </div>

      {/* 더보기/접기 버튼 */}
      <div className="mt-4 text-center">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-sm text-slate-600 underline underline-offset-2 hover:text-slate-800 transition-colors"
          aria-expanded={expanded}
        >
          {expanded ? '접기' : '더보기'}
        </button>
      </div>
    </article>
  );
}
