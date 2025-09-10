import { useState } from 'react';
import { Button } from '../components/common/atoms/Button';
import { ArrowLeft, ArrowRight, SearchIcon, SquareArrowOutUpRight, XIcon } from 'lucide-react';
import { IconButton } from '../components/common/atoms/IconButton';

export default function CalendarPage() {
  const [isSelected, setIsSelected] = useState(true);
  return (
    <>
      {/* <p>캘린더 페이지입니다</p> */}
      <h1 className="mt-7 mb-2">버튼 모음</h1>
      <div className="flex flex-wrap gap-2">
        <Button size="sm">기본 버튼</Button>
        <Button variant="outlined">더 보기</Button>
        <Button size="lg" endIcon={<SquareArrowOutUpRight size={15} />}>
          지원 공고 보러가기
        </Button>
        <Button selected={true} variant="tag">
          # 태그
        </Button>
        <Button variant="tag"># 태그는 여러개</Button>
        <Button selected={isSelected} variant="tag" onClick={() => setIsSelected(!isSelected)}>
          # 삼성전자
        </Button>
      </div>

      <h1 className="mt-7 mb-2">아이콘 버튼 모음</h1>
      <div className="flex flex-wrap gap-2">
        <IconButton size="sm">
          <SearchIcon />
        </IconButton>
        <IconButton size="md">
          <XIcon />
        </IconButton>
        <div className="flex gap-2">
          <IconButton aria-label="이전 페이지" variant="ghost" size="md">
            <ArrowLeft className="w-7 h-7" />
          </IconButton>
          <IconButton aria-label="다음 페이지" variant="ghost" size="md">
            <ArrowRight className="w-7 h-7" />
          </IconButton>
          <IconButton variant="plain" size="lg">
            <SearchIcon className="w-10 h-10" />
          </IconButton>
        </div>
      </div>
    </>
  );
}
