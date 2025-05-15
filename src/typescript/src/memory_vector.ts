import { HierarchicalNSW } from 'hnswlib-node';
// import { pipeline } from '@xenova/transformers'; // 改为动态导入
import fs from 'fs';
import path from 'path';
import os from 'os';
import { logger } from './logger';

type Metadata = Record<string, any>;

let pipeline: any;
async function getPipeline() {
  if (!pipeline) {
    pipeline = (await import('@xenova/transformers')).pipeline;
  }
  return pipeline;
}

export class MemoryVectorDB {
  private index: HierarchicalNSW;
  private metadatas: Metadata[] = [];
  private extractor: any = null;
  private readonly numDimensions: number;
  private readonly maxElements: number;
  private readonly spaceType: 'cosine' | 'l2' | 'ip';
  private readonly indexFile: string;
  private readonly metadataFile: string;
  private readonly modelName: string;

  constructor(options: {
    numDimensions: number,
    maxElements?: number,
    spaceType?: 'cosine' | 'l2' | 'ip',
    indexFile?: string,
    metadataFile?: string,
    modelName?: string,
    clearOnStart?: boolean
  }) {
    this.numDimensions = options.numDimensions;
    this.maxElements = options.maxElements || 10000;
    this.spaceType = options.spaceType || 'cosine';
    this.indexFile = options.indexFile || path.join(os.tmpdir(), 'nacos-mcp-router', 'my_hnsw_index.bin');
    this.metadataFile = options.metadataFile || path.join(os.tmpdir(), 'nacos-mcp-router', 'my_hnsw_metadata.json');
    this.modelName = options.modelName || 'Xenova/all-MiniLM-L6-v2';

    if (options.clearOnStart) {
      if (fs.existsSync(this.indexFile)) {
        fs.unlinkSync(this.indexFile);
        logger.info(`[MemoryVectorDB] 已清除索引文件: ${this.indexFile}`);
      }
      if (fs.existsSync(this.metadataFile)) {
        fs.unlinkSync(this.metadataFile);
        logger.info(`[MemoryVectorDB] 已清除元数据文件: ${this.metadataFile}`);
      }
    }

    this.index = new HierarchicalNSW(this.spaceType, this.numDimensions);

    if (fs.existsSync(this.indexFile) && fs.existsSync(this.metadataFile)) {
      logger.info(`[MemoryVectorDB] 加载已有索引: ${this.indexFile} 和元数据: ${this.metadataFile}`);
      this.index.readIndexSync(this.indexFile);
      this.metadatas = JSON.parse(fs.readFileSync(this.metadataFile, 'utf-8'));
    } else {
      logger.info(`[MemoryVectorDB] 初始化新索引, 最大元素数: ${this.maxElements}`);
      this.index.initIndex(this.maxElements);
    }
  }

  private async getEmbedding(text: string): Promise<number[]> {
    if (!this.extractor) {
      const _pipeline = await getPipeline();
      this.extractor = await _pipeline('feature-extraction', this.modelName);
    }
    const output = await this.extractor(text, { pooling: 'mean', normalize: true });
    return Array.from(output.data);
  }

  public async add(text: string, metadata: Metadata = {}) {
    logger.info(`[MemoryVectorDB] 添加文本到向量库: ${text.slice(0, 30)}...`);
    const vector = await this.getEmbedding(text);
    const label = this.index.getCurrentCount();
    this.index.addPoint(vector, label);
    this.metadatas[label] = { ...metadata, text };
    logger.info(`[MemoryVectorDB] 添加完成，label: ${label}`);
  }

  public async search(query: string, k: number = 5) {
    logger.info(`[MemoryVectorDB] 搜索: ${query.slice(0, 30)}...，topK=${k}`);
    const queryVector = await this.getEmbedding(query);
    const results = this.index.searchKnn(queryVector, k);
    logger.info(`[MemoryVectorDB] 搜索完成，返回${results.neighbors.length}条结果`);
    return results.neighbors.map((label: number, i: number) => ({
      metadata: this.metadatas[label],
      label,
      distance: results.distances[i],
      similarity: 1 - results.distances[i]
    }));
  }

  public save() {
    // 确保父目录存在
    const indexDir = path.dirname(this.indexFile);
    const metadataDir = path.dirname(this.metadataFile);
    if (!fs.existsSync(indexDir)) {
      fs.mkdirSync(indexDir, { recursive: true });
    }
    if (!fs.existsSync(metadataDir)) {
      fs.mkdirSync(metadataDir, { recursive: true });
    }
    this.index.writeIndexSync(this.indexFile);
    fs.writeFileSync(this.metadataFile, JSON.stringify(this.metadatas, null, 2));
    logger.info(`[MemoryVectorDB] 索引和元数据已保存到: ${this.indexFile}, ${this.metadataFile}`);
  }

  public load() {
    if (fs.existsSync(this.indexFile) && fs.existsSync(this.metadataFile)) {
      this.index.readIndexSync(this.indexFile);
      this.metadatas = JSON.parse(fs.readFileSync(this.metadataFile, 'utf-8'));
      logger.info(`[MemoryVectorDB] 已加载索引和元数据`);
    } else {
      logger.info(`[MemoryVectorDB] 未找到索引或元数据文件，无法加载`);
    }
  }

  public getCount() {
    return this.index.getCurrentCount();
  }
} 