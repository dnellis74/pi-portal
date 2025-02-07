import React, { useState, useMemo, useCallback } from 'react';
import Tree from 'rc-tree';
import styled from '@emotion/styled';
import 'rc-tree/assets/index.css';

const TreeContainer = styled.div`
  height: 100vh;
  padding: 20px;
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 8px;
  margin-bottom: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
`;

const VirtualizedTree = () => {
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [checkedKeys, setCheckedKeys] = useState([]);
  const [searchValue, setSearchValue] = useState('');
  const [treeData, setTreeData] = useState([]);
  const [loading, setLoading] = useState(false);

  // Memoized function to fetch children
  const loadData = useCallback(async (treeNode) => {
    setLoading(true);
    try {
      // Simulate API call
      const response = await new Promise((resolve) => 
        setTimeout(() => {
          resolve([...Array(5)].map((_, index) => ({
            key: `${treeNode.key}-${index}`,
            title: `Child ${index} of ${treeNode.title}`,
            isLeaf: false,
          })));
        }, 1000)
      );

      setTreeData((prevData) => {
        const updateTreeData = (list, key, children) => {
          return list.map((node) => {
            if (node.key === key) {
              return { ...node, children };
            }
            if (node.children) {
              return {
                ...node,
                children: updateTreeData(node.children, key, children),
              };
            }
            return node;
          });
        };
        return updateTreeData(prevData, treeNode.key, response);
      });
    } finally {
      setLoading(false);
    }
  }, []);

  // Initialize root nodes
  useMemo(() => {
    const rootNodes = [...Array(10)].map((_, index) => ({
      key: `${index}`,
      title: `Node ${index}`,
      isLeaf: false,
    }));
    setTreeData(rootNodes);
  }, []);

  // Filter nodes based on search
  const filteredTreeData = useMemo(() => {
    if (!searchValue) return treeData;

    const filterNodes = (nodes) => {
      return nodes.map(node => {
        const matchesSearch = node.title.toLowerCase().includes(searchValue.toLowerCase());
        const children = node.children ? filterNodes(node.children) : [];
        
        if (matchesSearch || children.length > 0) {
          return {
            ...node,
            children: children.length > 0 ? children : undefined
          };
        }
        return null;
      }).filter(Boolean);
    };

    return filterNodes(treeData);
  }, [treeData, searchValue]);

  const handleExpand = useCallback((keys) => {
    setExpandedKeys(keys);
  }, []);

  const handleCheck = useCallback((keys) => {
    setCheckedKeys(keys);
  }, []);

  return (
    <TreeContainer>
      <SearchInput
        placeholder="Search nodes..."
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
      />
      <Tree
        checkable
        loadData={loadData}
        treeData={filteredTreeData}
        expandedKeys={expandedKeys}
        checkedKeys={checkedKeys}
        onExpand={handleExpand}
        onCheck={handleCheck}
        height={600}
        itemHeight={28}
        virtual
        loading={loading}
      />
    </TreeContainer>
  );
};

export default VirtualizedTree; 